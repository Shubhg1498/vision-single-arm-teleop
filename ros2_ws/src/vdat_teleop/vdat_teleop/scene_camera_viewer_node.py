import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


def image_msg_to_bgr(msg: Image):
    if msg.encoding in ("rgb8", "bgr8"):
        channels = 3
    elif msg.encoding in ("rgba8", "bgra8"):
        channels = 4
    else:
        return None

    arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.width, channels)
    if msg.encoding == "rgb8":
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    if msg.encoding == "rgba8":
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
    if msg.encoding == "bgra8":
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    return arr.copy()


class SceneCameraViewerNode(Node):
    def __init__(self):
        super().__init__("scene_camera_viewer_node")

        self.declare_parameter(
            "camera_topics",
            [
                "/scene_camera_overview",
                "/scene_camera_side",
                "/scene_camera_gripper",
                "/scene_camera_table_top",
            ],
        )
        self.declare_parameter(
            "labels",
            ["Overview", "Side", "Gripper", "Table Top"],
        )
        self.declare_parameter("display_scale", 0.55)
        self.declare_parameter("refresh_hz", 15.0)

        topics = list(self.get_parameter("camera_topics").value)
        labels = list(self.get_parameter("labels").value)
        self.display_scale = float(self.get_parameter("display_scale").value)

        if len(labels) != len(topics):
            labels = [t.split("/")[-1] for t in topics]

        self.labels = labels
        self.frames = {topic: None for topic in topics}

        for topic in topics:
            self.create_subscription(
                Image,
                topic,
                lambda msg, t=topic: self._on_image(msg, t),
                10,
            )

        refresh_hz = float(self.get_parameter("refresh_hz").value)
        self.create_timer(1.0 / refresh_hz, self._on_timer)

        self.get_logger().info("Scene camera viewer started.")
        for topic, label in zip(topics, labels):
            self.get_logger().info(f"  {label}: {topic}")

    def _on_image(self, msg: Image, topic: str):
        frame = image_msg_to_bgr(msg)
        if frame is not None:
            self.frames[topic] = frame

    def _on_timer(self):
        tiles = []
        topic_list = list(self.frames.keys())
        for i, topic in enumerate(topic_list):
            frame = self.frames[topic]
            label = self.labels[i] if i < len(self.labels) else topic

            if frame is None:
                tile = np.zeros((240, 320, 3), dtype=np.uint8)
                cv2.putText(
                    tile,
                    f"{label}: waiting...",
                    (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (200, 200, 200),
                    1,
                )
            else:
                tile = frame.copy()
                cv2.rectangle(tile, (0, 0), (tile.shape[1] - 1, 28), (0, 0, 0), -1)
                cv2.putText(
                    tile,
                    label,
                    (8, 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

            if self.display_scale != 1.0:
                tile = cv2.resize(
                    tile,
                    None,
                    fx=self.display_scale,
                    fy=self.display_scale,
                    interpolation=cv2.INTER_AREA,
                )
            tiles.append(tile)

        if not tiles:
            return

        if len(tiles) == 1:
            grid = tiles[0]
        elif len(tiles) == 2:
            grid = np.hstack(tiles)
        elif len(tiles) == 3:
            top = np.hstack(tiles[:2])
            bottom = tiles[2]
            if bottom.shape[1] < top.shape[1]:
                pad = top.shape[1] - bottom.shape[1]
                bottom = cv2.copyMakeBorder(
                    bottom, 0, 0, 0, pad, cv2.BORDER_CONSTANT, value=(20, 20, 20)
                )
            elif bottom.shape[1] > top.shape[1]:
                pad = bottom.shape[1] - top.shape[1]
                top = cv2.copyMakeBorder(
                    top, 0, 0, 0, pad, cv2.BORDER_CONSTANT, value=(20, 20, 20)
                )
            grid = np.vstack([top, bottom])
        else:
            rows = []
            for i in range(0, len(tiles), 2):
                row = tiles[i : i + 2]
                if len(row) == 1:
                    row.append(
                        np.full(row[0].shape, 20, dtype=np.uint8),
                    )
                rows.append(np.hstack(row))
            grid = np.vstack(rows)

        cv2.imshow("Scene Cameras (Teleop)", grid)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            self.get_logger().info("Quit requested from scene camera viewer.")
            rclpy.shutdown()


def main():
    rclpy.init()
    node = SceneCameraViewerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
