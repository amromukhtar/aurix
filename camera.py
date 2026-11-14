#!/usr/bin/env python3
"""
Trigger-based lightweight object detection for Raspberry Pi 5
Uses system OpenCV and picamera2
"""

import cv2
import numpy as np
from picamera2 import Picamera2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class ObjectDetector:
    def __init__(self, confidence_threshold=0.5, preview_size=(640, 480)):
        self.confidence_threshold = confidence_threshold

        # COCO class labels
        self.CLASSES = [
            "background",
            "aeroplane",
            "bicycle",
            "bird",
            "boat",
            "bottle",
            "bus",
            "car",
            "cat",
            "chair",
            "cow",
            "diningtable",
            "dog",
            "horse",
            "motorbike",
            "person",
            "pottedplant",
            "sheep",
            "sofa",
            "train",
            "tvmonitor",
        ]

        # Initialize camera
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": preview_size})
        self.picam2.configure(config)
        self.picam2.start()

        # Load model
        print("Loading MobileNet SSD model...")
        self.net = cv2.dnn.readNetFromCaffe(
            os.path.join(BASE_DIR, "camera_lib/MobileNetSSD_deploy.prototxt"),
            os.path.join(BASE_DIR, "camera_lib/MobileNetSSD_deploy.caffemodel"),
        )

    def detect(self, draw=False):
        """
        Trigger detection once and return detected objects

        Returns:
            detections_list: [
                {
                    "class": "person",
                    "confidence": 0.87,
                    "box": (x1, y1, x2, y2)
                },
                ...
            ]
        """
        frame = self.picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        h, w = frame.shape[:2]

        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
        )

        self.net.setInput(blob)
        detections = self.net.forward()

        results = []

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence >= self.confidence_threshold:
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype(int)

                detection_info = {
                    "class": self.CLASSES[idx],
                    "confidence": float(confidence),
                    "box": (x1, y1, x2, y2),
                }
                results.append(detection_info)

                if draw:
                    label = f"{self.CLASSES[idx]}: {confidence*100:.1f}%"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )

        if draw:
            cv2.imshow("Triggered Detection", frame)
            cv2.waitKey(1)

        IMG_W, IMG_H = 640, 480

        formatted_info = []
        for obj in results:
            # Convert np.int64 to standard int
            x1, y1, x2, y2 = [int(coord) for coord in obj["box"]]

            # Normalize to 1000-unit scale
            norm_box = [
                int(y1 * 1000 / IMG_H),  # ymin
                int(x1 * 1000 / IMG_W),  # xmin
                int(y2 * 1000 / IMG_H),  # ymax
                int(x2 * 1000 / IMG_W),  # xmax
            ]
            formatted_info.append(
                f"{obj['class']} [ymin, xmin, ymax, xmax]: {norm_box}"
            )

        return formatted_info

    def stop(self):
        self.picam2.stop()
        cv2.destroyAllWindows()
        print("Detector stopped")
