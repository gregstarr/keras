import numpy as np
import pytest
from tensorflow import data as tf_data

from keras.src import backend
from keras.src import layers
from keras.src import testing


class RandAugmentTest(testing.TestCase):
    @pytest.mark.requires_trainable_backend
    def test_layer(self):
        self.run_layer_test(
            layers.RandAugment,
            init_kwargs={
                "value_range": (0, 255),
                "num_ops": 2,
                "factor": 1,
                "interpolation": "nearest",
                "seed": 1,
                "data_format": "channels_last",
            },
            input_shape=(8, 3, 4, 3),
            supports_masking=False,
            expected_output_shape=(8, 3, 4, 3),
        )

    def test_rand_augment_inference(self):
        seed = 3481
        layer = layers.RandAugment()

        np.random.seed(seed)
        inputs = np.random.randint(0, 255, size=(224, 224, 3))
        output = layer(inputs, training=False)
        self.assertAllClose(inputs, output)

    def test_rand_augment_basic(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_data = np.random.random((2, 8, 8, 3))
        else:
            input_data = np.random.random((2, 3, 8, 8))
        layer = layers.RandAugment(data_format=data_format)

        augmented_image = layer(input_data)
        self.assertEqual(augmented_image.shape, input_data.shape)

    def test_rand_augment_no_operations(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_data = np.random.random((2, 8, 8, 3))
        else:
            input_data = np.random.random((2, 3, 8, 8))
        layer = layers.RandAugment(num_ops=0, data_format=data_format)

        augmented_image = layer(input_data)
        self.assertAllClose(
            backend.convert_to_numpy(augmented_image), input_data
        )

    def test_random_augment_randomness(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_data = np.random.random((2, 8, 8, 3))
        else:
            input_data = np.random.random((2, 3, 8, 8))

        layer = layers.RandAugment(num_ops=11, data_format=data_format)
        augmented_image = layer(input_data)

        self.assertNotAllClose(
            backend.convert_to_numpy(augmented_image), input_data
        )

    def test_tf_data_compatibility(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_data = np.random.random((2, 8, 8, 3))
        else:
            input_data = np.random.random((2, 3, 8, 8))
        layer = layers.RandAugment(data_format=data_format)

        ds = tf_data.Dataset.from_tensor_slices(input_data).batch(2).map(layer)
        for output in ds.take(1):
            output.numpy()

    def test_rand_augment_tf_data_bounding_boxes(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            image_shape = (1, 10, 8, 3)
        else:
            image_shape = (1, 3, 10, 8)
        input_image = np.random.random(image_shape)
        bounding_boxes = {
            "boxes": np.array(
                [
                    [
                        [2, 1, 4, 3],
                        [6, 4, 8, 6],
                    ]
                ]
            ),
            "labels": np.array([[1, 2]]),
        }

        input_data = {"images": input_image, "bounding_boxes": bounding_boxes}

        ds = tf_data.Dataset.from_tensor_slices(input_data)
        layer = layers.RandAugment(
            data_format=data_format,
            seed=42,
            bounding_box_format="xyxy",
        )
        ds.map(layer)
    
    def test_rand_augment_tf_graph_mode(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_data = np.random.random((4, 8, 8, 3))
        else:
            input_data = np.random.random((4, 3, 8, 8))
        layer = layers.RandAugment(data_format=data_format, seed=42, num_ops=1)

        # using tf.data.Dataset.map applies the function in graph mode
        # lambda gets shuffled transform index
        ds = tf_data.Dataset.from_tensor_slices(input_data).batch(2).map(
            lambda x: layer.get_random_transformation(x)[0]
        )
        results = []
        for output in ds:
            results.append(output.numpy())
        self.assertFalse(np.all(results[0] == results[1]))

    def test_rand_augment_tf_graph_mode_2(self):
        data_format = backend.config.image_data_format()
        if data_format == "channels_last":
            input_data = np.random.random((8, 8, 8, 3))
        else:
            input_data = np.random.random((8, 3, 8, 8))
        layer = layers.RandAugment(data_format=data_format, seed=42, num_ops=1)

        # using tf.data.Dataset.map applies the function in graph mode
        # lambda gets shuffled transform index
        ds = tf_data.Dataset.from_tensor_slices(input_data).batch(2).map(
            lambda x: layer.get_random_transformation(x)[0]
        )
        results = set()
        for output in ds:
            for i in output.numpy():
                results.add(layer._AUGMENT_LAYERS[i])
        print(results)
        self.assertTrue(len(results) > 1)
