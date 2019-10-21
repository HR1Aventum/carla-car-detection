# Based on https://github.com/EdjeElectronics/TensorFlow-Object-Detection-API-Tutorial-Train-Multiple-Objects-Windows-10/blob/master/Object_detection_image.py

import sys
from pathlib import Path
sys.path.append("./models/research/object_detection/")
sys.path.append("./models/research/")

import os
import cv2
import numpy as np
import tensorflow as tf
from utils import label_map_util
from utils import visualization_utils as vis_util

def process_image(name, frame_number, frame, sess, output_path, tensors, category_index, min_score_threshold):
    image_tensor, detection_boxes, detection_scores, detection_classes, num_detections = tensors
    
    frame_expanded = np.expand_dims(frame, axis=0)   
    (boxes, scores, classes, num) = sess.run(
        [detection_boxes, detection_scores, detection_classes, num_detections],
        feed_dict={image_tensor: frame_expanded})
    vis_util.visualize_boxes_and_labels_on_image_array(
        frame,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=2,
        min_score_thresh=min_score_threshold)
    output_file = os.path.join(output_path, f"{name}_frame_{frame_number}.png")
    vis_util.save_image_array_as_png(frame, output_file)
    return frame
    

def process_video(model_path, labelmap_path, video_path, min_score_threshold, output_path, display_video):
    NUM_CLASSES = 5
    video_name = Path(video_path).stem
    
    label_map = label_map_util.load_labelmap(labelmap_path)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)
    
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(model_path, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')
        
        sess = tf.Session(graph=detection_graph)
        
        # Define input and output tensors (i.e. data) for the object detection classifier
        image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
        detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
        detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
        detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
        num_detections = detection_graph.get_tensor_by_name('num_detections:0')
        tensors = (image_tensor, detection_boxes, detection_scores, detection_classes, num_detections)
        
        # Open video file
        video = cv2.VideoCapture(video_path)

        frame_number = 0
        while(video.isOpened()):
            ret, frame = video.read()
            frame_expanded = np.expand_dims(frame, axis=0)
            process_image(video_name, frame_number, frame, sess, output_path, tensors, category_index, min_score_threshold)
            
            (boxes, scores, classes, num) = sess.run(
                [detection_boxes, detection_scores, detection_classes, num_detections],
                feed_dict={image_tensor: frame_expanded})

            height, width, channels = frame.shape
            
            vis_util.visualize_boxes_and_labels_on_image_array(
                frame,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index,
                use_normalized_coordinates=True,
                line_thickness=2,
                min_score_thresh=min_score_threshold)

            print("Frame:", frame_number)
            for box, score in zip(np.squeeze(boxes), np.squeeze(scores)):
                if score >= min_score_threshold:
                    print("Box: ", box, "Score: ", score)

            frame_number += 1
            if display_video:
                cv2.imshow('Object detector', frame)
                if cv2.waitKey(1) == ord('q'):
                    break

        # Clean up
        video.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', help='Path to the frozen inference graph file', required=True)
    parser.add_argument('--label_path', help='Path to the labelmap file', required=True)
    parser.add_argument('--video_path', help='Path to the video', required=True)
    parser.add_argument('--min_threshold', type=int, help='Minimum score threshold for a bounding box to be drawn', default=0.7)
    parser.add_argument('--output_path', help='Path for storing output images and/or logs', required=True)
    parser.add_argument('--display_video', default=False)

    args = parser.parse_args()
    # Name of the directory containing the object detection module we're using
    process_video(args.model_path,
                  args.label_path,
                  args.video_path,
                  args.min_threshold,
                  args.output_path,
                  args.display_video)