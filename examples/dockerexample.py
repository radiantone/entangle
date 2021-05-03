from entangle.logging.debug import logging
from entangle.containers import docker
from entangle.process import process
from entangle.workflow import workflow


@process
@docker(image="tensorflow/tensorflow:latest-gpu")
def one():
    import tensorflow as tf
    return tf.reduce_sum(tf.random.normal([1000, 1000]))


@process
@docker(image="tensorflow/tensorflow:latest-gpu", packages=['tensorflow_datasets'])
def train():
    import tensorflow as tf
    import tensorflow_datasets as tfds

    (ds_train, ds_test), ds_info = tfds.load(
        'mnist',
        split=['train', 'test'],
        shuffle_files=True,
        as_supervised=True,
        with_info=True,
    )

    def normalize_img(image, label):
        return tf.cast(image, tf.float32) / 255., label

    ds_train = ds_train.map(
        normalize_img, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    ds_train = ds_train.cache()
    ds_train = ds_train.shuffle(ds_info.splits['train'].num_examples)
    ds_train = ds_train.batch(128)
    ds_train = ds_train.prefetch(tf.data.experimental.AUTOTUNE)

    ds_test = ds_test.map(
        normalize_img, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    ds_test = ds_test.batch(128)
    ds_test = ds_test.cache()
    ds_test = ds_test.prefetch(tf.data.experimental.AUTOTUNE)

    model = tf.keras.models.Sequential([
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10)
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy()],
    )

    model.fit(
        ds_train,
        epochs=6,
        verbose=0,
        validation_data=ds_test,
    )

    return model.summary()


# wait is how long I will wait on dependent values. timeout is how long I should take
@process(wait=20)
def values(*args):
    values = [arg for arg in args]

    return values


o = values(
    one(),
    train()
)
print("RESULT:", o())
