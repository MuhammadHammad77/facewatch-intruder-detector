"""
In-Memory Face Encoding Cache
──────────────────────────────
Why: Comparing 128D encodings against DB on every frame = too slow.
Solution: Load all known encodings into RAM at startup.
          Re-call FaceEncodingCache.refresh() after admin adds/deletes a face.
"""

import asyncio
import numpy as np
from db.supabase_client import fetch_all_faces


class FaceEncodingCache:
    """
    Class-level cache. All video stream workers share the same loaded encodings.

    Structure:
        encodings : list[np.ndarray]   — 128D float arrays, one per face
        names     : list[str]          — parallel list of names
        ids       : list[str]          — parallel list of face IDs (UUIDs)
    """
    encodings: list[np.ndarray] = []
    names:     list[str]        = []
    ids:       list[str]        = []

    @classmethod
    async def refresh(cls):
        """
        Pull latest face data from Supabase and rebuild in-memory cache.
        Call this on startup and after any face registration/deletion.
        """
        loop = asyncio.get_event_loop()
        # Run DB call in thread pool (supabase-py is sync)
        faces = await loop.run_in_executor(None, fetch_all_faces)

        cls.encodings = []
        cls.names = []
        cls.ids = []

        for face in faces:
            encoding_list = face.get("encoding")
            if encoding_list and len(encoding_list) == 128:
                cls.encodings.append(np.array(encoding_list, dtype=np.float64))
                cls.names.append(face["name"])
                cls.ids.append(face["id"])

        print(f"🔄 Cache refreshed: {len(cls.encodings)} known faces loaded.")

    @classmethod
    def is_empty(cls) -> bool:
        return len(cls.encodings) == 0
