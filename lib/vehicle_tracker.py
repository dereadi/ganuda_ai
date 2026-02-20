import numpy as np
from collections import OrderedDict
from scipy.spatial import distance as dist
from typing import List, Dict, Tuple

class VehicleTracker:
    """
    A class to track vehicles based on their bounding box centroids.
    
    Attributes:
        next_id (int): The next unique identifier for a vehicle.
        objects (OrderedDict): A dictionary mapping vehicle IDs to their centroids.
        disappeared (OrderedDict): A dictionary mapping vehicle IDs to the number of consecutive frames they have been missed.
        max_disappeared (int): The maximum number of consecutive frames a vehicle can be missed before being deregistered.
    """

    def __init__(self, max_disappeared: int = 30):
        """
        Initializes a new instance of the VehicleTracker class.

        :param max_disappeared: The maximum number of consecutive frames a vehicle can be missed before being deregistered.
        """
        self.next_id: int = 0
        self.objects: OrderedDict[int, Tuple[int, int]] = OrderedDict()
        self.disappeared: OrderedDict[int, int] = OrderedDict()
        self.max_disappeared: int = max_disappeared

    def register(self, centroid: Tuple[int, int]) -> None:
        """
        Registers a new vehicle with the given centroid.

        :param centroid: The centroid coordinates of the vehicle.
        """
        self.objects[self.next_id] = centroid
        self.disappeared[self.next_id] = 0
        self.next_id += 1

    def deregister(self, object_id: int) -> None:
        """
        Deregisters a vehicle with the given ID.

        :param object_id: The ID of the vehicle to deregister.
        """
        del self.objects[object_id]
        del self.disappeared[object_id]

    def update(self, rects: List[Tuple[int, int, int, int]]) -> Dict[int, Tuple[int, int]]:
        """
        Updates the tracker with the current bounding boxes.

        :param rects: A list of bounding boxes in the format [(x, y, w, h), ...].
        :return: A dictionary mapping vehicle IDs to their updated centroids.
        """
        if len(rects) == 0:
            for oid in list(self.disappeared.keys()):
                self.disappeared[oid] += 1
                if self.disappeared[oid] > self.max_disappeared:
                    self.deregister(oid)
            return self.objects

        centroids = np.zeros((len(rects), 2), dtype="int")
        for i, (x, y, w, h) in enumerate(rects):
            centroids[i] = (x + w // 2, y + h // 2)

        if len(self.objects) == 0:
            for c in centroids:
                self.register(c)
        else:
            obj_ids = list(self.objects.keys())
            obj_centroids = list(self.objects.values())
            D = dist.cdist(np.array(obj_centroids), centroids)
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            used_rows, used_cols = set(), set()
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                oid = obj_ids[row]
                self.objects[oid] = centroids[col]
                self.disappeared[oid] = 0
                used_rows.add(row)
                used_cols.add(col)
            for col in set(range(len(centroids))) - used_cols:
                self.register(centroids[col])
        return self.objects