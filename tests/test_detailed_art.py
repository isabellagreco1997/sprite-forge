import unittest
import numpy as np
from spriteforge import Sprite, frame_report


class DetailedArtTests(unittest.TestCase):
    def test_256_color_dump_round_trip(self):
        a = np.zeros((16, 16, 4), dtype=np.uint8)
        a[..., 0] = np.arange(256, dtype=np.uint8).reshape(16, 16)
        a[..., 1] = 90
        a[..., 3] = 255
        source = Sprite(a)
        dump = source.dump(with_palette=False)
        self.assertNotIn('?', dump)
        target = Sprite(np.zeros_like(a), source.pal)
        for y, line in enumerate(dump.splitlines()[1:]):
            target.paint(y, 0, line[4:])
        np.testing.assert_array_equal(target.a, a)

    def test_large_unquantized_palette_fails_explicitly(self):
        a = np.zeros((1, 257, 4), dtype=np.uint8)
        a[0, :256, 0] = np.arange(256, dtype=np.uint8)
        a[0, 256, 1] = 1
        a[..., 3] = 255
        with self.assertRaisesRegex(ValueError, 'quantize'):
            Sprite(a)

    def test_original_symbol_assignments_remain_compatible(self):
        a = np.zeros((1, 62, 4), dtype=np.uint8)
        a[0, :, 0] = np.arange(62)
        a[..., 3] = 255
        self.assertEqual(''.join(Sprite(a).pal), '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

    def test_report_distinguishes_allowed_edits_and_artifacts(self):
        ref = np.zeros((8, 8, 4), dtype=np.uint8)
        ref[2:6, 2:6] = (100, 50, 20, 255)
        frame = ref.copy()
        frame[3, 3] = (200, 50, 20, 255)
        frame[4, 5, 3] = 100
        frame[0, 0] = (100, 50, 20, 255)
        allowed = np.zeros((8, 8), dtype=bool)
        allowed[3, 3] = True
        result = frame_report(ref, [frame], allowed)[0]
        self.assertEqual(result['changed_pixels'], 3)
        self.assertEqual(result['outside_mask_pixels'], 2)
        self.assertEqual(result['partial_alpha_pixels'], 1)
        self.assertEqual(result['new_border_pixels'], 1)
        self.assertEqual(result['new_colors'], [[200, 50, 20]])
        self.assertIn([0, 0], result['isolated_pixels'])

    def test_transparent_rgb_is_not_visible_change(self):
        ref = np.zeros((2, 2, 4), dtype=np.uint8)
        frame = ref.copy(); frame[0, 0, :3] = 255
        self.assertEqual(frame_report(ref, [frame])[0]['changed_pixels'], 0)

    def test_mismatched_size_is_reported(self):
        result = frame_report(np.zeros((2, 2, 4), dtype=np.uint8), [np.zeros((3, 3, 4), dtype=np.uint8)])[0]
        self.assertFalse(result['size_matches'])

    def test_mask_shape_is_checked(self):
        with self.assertRaisesRegex(ValueError, 'match'):
            frame_report(np.zeros((2, 2, 4), dtype=np.uint8), [], np.zeros((3, 3), dtype=bool))


if __name__ == '__main__':
    unittest.main()
