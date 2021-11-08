import numpy as np
from tensorflow import keras
from tensorflow.keras import layers, optimizers, losses, metrics

# from this answer: https://github.com/tensorflow/tensorflow/issues/24496#issuecomment-464909727
from tensorflow.compat.v1 import ConfigProto
from tensorflow.compat.v1 import InteractiveSession
config = ConfigProto()
config.gpu_options.allow_growth = True
session = InteractiveSession(config=config)

EMBEDDING_SIZE = 4
VOCAB_SIZE = 3
N_EPOCHS = 5
N_CLASSES = 2

def get_data():
    X = np.asarray([
        [1, 2, 3, 0, 0],
        [3, 1, 0, 0, 0],
        [2, 2, 2, 2, 2]
    ])

    Y = np.eye(N_CLASSES)[np.random.choice(N_CLASSES, X.shape)].astype(np.int32)
    return X, Y

def mask_test():
    X, Y = get_data()
    input_length = X.shape[1]
    inputs = keras.Input((input_length,))
    embed = layers.Embedding(VOCAB_SIZE + 1, EMBEDDING_SIZE, input_length=input_length, trainable=True, mask_zero=True)(inputs)
    lstm = layers.LSTM(EMBEDDING_SIZE, return_sequences=True)(embed)
    outputs = layers.Dense(2, activation='softmax')(lstm)
    model = keras.Model(inputs=inputs, outputs=outputs)
    model_metrics = [metrics.Recall(class_id=0)]  # this doesn't work but [metrics.Recall()] does
    model.compile(optimizer=optimizers.Adam(), loss=losses.BinaryCrossentropy(from_logits=False), metrics=model_metrics)
    model.fit(X, Y, epochs=N_EPOCHS)


if __name__ == "__main__":
    mask_test()