import os
import random
import shutil
import requests
import time
from pycocotools.coco import COCO
from ultralytics import YOLO
from sklearn.model_selection import train_test_split

def download_balanced_coco_images(classes, images_per_class=400, output_dir="coco_subset", max_retries=3):
    """Download equal number of images for each specified class"""
    os.makedirs(f"{output_dir}/images", exist_ok=True)
    os.makedirs(f"{output_dir}/labels", exist_ok=True)

    ann_file = "annotations/instances_train2017.json"  # Update path if needed
    coco = COCO(ann_file)

    class_ids = coco.getCatIds(catNms=classes)
    class_img_counts = {class_id: 0 for class_id in class_ids}
    downloaded_images = set()  # To avoid duplicate downloads

    for class_id in class_ids:
        class_name = coco.loadCats(class_id)[0]['name']
        print(f"\nProcessing class: {class_name}")
        img_ids = coco.getImgIds(catIds=class_id)
        random.shuffle(img_ids)
        
        for img_id in img_ids:
            if class_img_counts[class_id] >= images_per_class:
                break
                
            if img_id in downloaded_images:
                continue  
                
            img_info = coco.loadImgs(img_id)[0]
            img_url = f"http://images.cocodataset.org/train2017/{img_info['file_name']}"
            img_path = f"{output_dir}/images/{img_info['file_name']}"
            label_path = f"{output_dir}/labels/{img_info['file_name'].replace('.jpg', '.txt')}"

            if os.path.exists(img_path) and os.path.exists(label_path):
                downloaded_images.add(img_id)
                class_img_counts[class_id] += 1
                continue

            for attempt in range(max_retries):
                try:
                    response = requests.get(img_url, stream=True, timeout=30)
                    response.raise_for_status()
                    with open(img_path, "wb") as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    
                    ann_ids = coco.getAnnIds(imgIds=img_id, catIds=class_ids)
                    annotations = coco.loadAnns(ann_ids)
                    with open(label_path, "w") as f:
                        for ann in annotations:
                            if ann["category_id"] in class_ids:  # Only include our target classes
                                class_idx = class_ids.index(ann["category_id"])
                                x, y, w, h = ann["bbox"]
                                x_center = (x + w/2) / img_info["width"]
                                y_center = (y + h/2) / img_info["height"]
                                w_norm = w / img_info["width"]
                                h_norm = h / img_info["height"]
                                f.write(f"{class_idx} {x_center} {y_center} {w_norm} {h_norm}\n")
                    
                    downloaded_images.add(img_id)
                    class_img_counts[class_id] += 1
                    print(f"Downloaded {class_img_counts[class_id]}/{images_per_class} for {class_name}: {img_info['file_name']}")
                    break  # Success
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed for {img_info['file_name']}: {str(e)}")
                    if attempt == max_retries - 1:
                        print(f"Skipping after {max_retries} attempts")
                    time.sleep(2)  # Delay between retries

    print("\nDownload summary:")
    for class_id, count in class_img_counts.items():
        class_name = coco.loadCats(class_id)[0]['name']
        print(f"{class_name}: {count} images")

def split_train_test(data_dir="coco_subset", test_size=0.2):
    """Split dataset into train and test sets while maintaining class balance"""
    images = [f for f in os.listdir(f"{data_dir}/images") if f.endswith(".jpg")]
    
    image_classes = []
    for img in images:
        label_file = f"{data_dir}/labels/{img.replace('.jpg', '.txt')}"
        if os.path.exists(label_file):
            with open(label_file, 'r') as f:
                classes_in_image = [int(line.split()[0]) for line in f.readlines()]
            if classes_in_image:
                image_classes.append(max(set(classes_in_image), key=classes_in_image.count))
            else:
                image_classes.append(-1)  # No objects
        else:
            image_classes.append(-1)
    
    train_images, test_images = train_test_split(
        images, 
        test_size=test_size, 
        random_state=42,
        stratify=image_classes
    )

    for split in ["train", "test"]:
        os.makedirs(f"{data_dir}/{split}/images", exist_ok=True)
        os.makedirs(f"{data_dir}/{split}/labels", exist_ok=True)

    for img in train_images:
        shutil.move(f"{data_dir}/images/{img}", f"{data_dir}/train/images/{img}")
        shutil.move(f"{data_dir}/labels/{img.replace('.jpg', '.txt')}", f"{data_dir}/train/labels/{img.replace('.jpg', '.txt')}")

    for img in test_images:
        shutil.move(f"{data_dir}/images/{img}", f"{data_dir}/test/images/{img}")
        shutil.move(f"{data_dir}/labels/{img.replace('.jpg', '.txt')}", f"{data_dir}/test/labels/{img.replace('.jpg', '.txt')}")

def train_yolov8(data_dir="coco_subset"):
    """Train YOLOv8 model on the balanced dataset"""
    class_names = ["person", "chair", "knife", "laptop", "scissors", "cell phone"]
    
    with open(f"{data_dir}/data.yaml", "w") as f:
        f.write(f"train: {os.path.abspath(data_dir)}/train/images\n")
        f.write(f"val: {os.path.abspath(data_dir)}/test/images\n")
        f.write(f"nc: {len(class_names)}\n")
        f.write(f"names: {class_names}\n")

    model = YOLO("yolov8n.pt")
    
    for k, v in model.named_parameters():
        if not k.startswith('model.22'):  # Freeze all except head
            v.requires_grad = False

    model.train(
        data=f"{data_dir}/data.yaml",
        epochs=25,
        imgsz=640,
        batch=16,
        patience=10,
        device='0' if os.getenv('CUDA_VISIBLE_DEVICES') else 'cpu',
        single_cls=False,
        cos_lr=True,  
        label_smoothing=0.1,  
        overlap_mask=True,
    )

    metrics = model.val()
    print(f"\nEvaluation Metrics:")
    print(f"mAP@0.5: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall: {metrics.box.mr:.4f}")
    print(f"F1 Score: {2 * (metrics.box.mp * metrics.box.mr) / (metrics.box.mp + metrics.box.mr):.4f}")

if __name__ == "__main__":
    target_classes = ["person", "chair", "knife", "laptop", "scissors", "cell phone"]
    
    print("Downloading balanced COCO images for selected classes...")
    download_balanced_coco_images(classes=target_classes, images_per_class=400)

    print("\nSplitting dataset with stratification...")
    split_train_test()

    print("\nTraining YOLOv8 on balanced dataset...")
    train_yolov8()

    print("\nTraining complete!")
