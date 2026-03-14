import streamlit as st
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras import layers, models, regularizers, optimizers
from tensorflow.keras.metrics import MeanAbsoluteError
from tensorflow.keras.models import Model
from tensorflow.keras import backend as K
import tensorflow as tf

from config import (
    AGE_MODEL_PATH,
    VAR_MODEL_PATH,
    LABEL_MODEL_PATH,
    AGE_MIN,
    AGE_MAX,
)

# Patch DepthwiseConv2D to drop the unsupported 'groups' arg
class DepthwiseConv2D(layers.DepthwiseConv2D):
    def __init__(self, *args, **kwargs):
        kwargs.pop("groups", None)
        super().__init__(*args, **kwargs)

# Rebuild MobileNetV3-Small with given hyperparameters
def build_age_model(input_shape=(224, 224, 3)):
    width_mult = 0.9996812193207757
    se_ratio = 5
    dropout_rate = 0.4751013759888731
    l2_reg = 1.1489665712499043e-06
    lr_init = 0.009768643728674135
    loss_fn = 'mse'

    def relu6(x):
        return tf.nn.relu6(x)

    def hard_swish(x):
        return x * relu6(x + 3) / 6.0

    def se_block(inputs):
        filters = inputs.shape[-1]
        x = layers.GlobalAveragePooling2D()(inputs)
        x = layers.Reshape((1, 1, filters))(x)
        x = layers.Conv2D(filters // se_ratio, 1,
                          activation='relu',
                          kernel_regularizer=regularizers.l2(l2_reg))(x)
        x = layers.Conv2D(filters, 1,
                          activation='hard_sigmoid',
                          kernel_regularizer=regularizers.l2(l2_reg))(x)
        return layers.Multiply()([inputs, x])

    def bottleneck(x, out_c, k, exp_c, stride, use_se, act, block_id):
        shortcut = x
        # Expand
        x = layers.Conv2D(exp_c, 1, padding='same', use_bias=False,
                          kernel_regularizer=regularizers.l2(l2_reg),
                          name=f"exp_{block_id}")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation(hard_swish if act == 'hswish' else relu6)(x)

        # Depthwise
        x = DepthwiseConv2D(k, stride, padding='same', use_bias=False,
                            depthwise_regularizer=regularizers.l2(l2_reg),
                            name=f"dw_{block_id}")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation(hard_swish if act == 'hswish' else relu6)(x)

        # SE
        if use_se:
            x = se_block(x)

        # Project
        x = layers.Conv2D(out_c, 1, padding='same', use_bias=False,
                          kernel_regularizer=regularizers.l2(l2_reg),
                          name=f"proj_{block_id}")(x)
        x = layers.BatchNormalization()(x)

        # Skip
        if stride == 1 and shortcut.shape[-1] == out_c:
            x = layers.Add()([x, shortcut])
        return x

    inputs = layers.Input(shape=input_shape)
    # Stem
    x = layers.Conv2D(int(16 * width_mult), 3, 2, 'same', use_bias=False,
                      kernel_regularizer=regularizers.l2(l2_reg))(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation(hard_swish)(x)

    # MobileNetV3-Small config scaled by width_mult
    cfg = [
        (3, int(16 * width_mult), int(16 * width_mult), True, 'relu', 2),
        (3, int(72 * width_mult), int(24 * width_mult), False, 'relu', 2),
        (3, int(88 * width_mult), int(24 * width_mult), False, 'relu', 1),
        (5, int(96 * width_mult), int(40 * width_mult), True, 'hswish', 2),
        (5, int(240 * width_mult), int(40 * width_mult), True, 'hswish', 1),
        (5, int(240 * width_mult), int(40 * width_mult), True, 'hswish', 1),
        (5, int(120 * width_mult), int(48 * width_mult), True, 'hswish', 1),
        (5, int(144 * width_mult), int(48 * width_mult), True, 'hswish', 1),
        (5, int(288 * width_mult), int(96 * width_mult), True, 'hswish', 2),
        (5, int(576 * width_mult), int(96 * width_mult), True, 'hswish', 1),
        (5, int(576 * width_mult), int(96 * width_mult), True, 'hswish', 1),
    ]

    for idx, (k, exp_c, out_c, us, act, s) in enumerate(cfg):
        x = bottleneck(x, out_c, k, exp_c, s, us, act, idx)

    # Head
    x = layers.Conv2D(int(576 * width_mult), 1, use_bias=False,
                      kernel_regularizer=regularizers.l2(l2_reg))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation(hard_swish)(x)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Flatten()(x)
    x = layers.Dropout(dropout_rate)(x)
    outputs = layers.Dense(1)(x)

    model = Model(inputs, outputs, name="MobileNetV3_Small_Scratch")
    model.compile(
        optimizer=optimizers.Adam(learning_rate=lr_init),
        loss=loss_fn,
        metrics=[MeanAbsoluteError(name='mae')]
    )
    return model


@st.cache_resource
def load_models():
    custom = {"DepthwiseConv2D": DepthwiseConv2D}

    # Build age model architecture and load weights
    age_m = build_age_model()
    age_m.load_weights(str(AGE_MODEL_PATH))

    # Load variety and label full models
    var_m = load_model(str(VAR_MODEL_PATH), custom_objects=custom, compile=False)
    lbl_m = load_model(str(LABEL_MODEL_PATH), custom_objects=custom, compile=False)

    return age_m, var_m, lbl_m


def preprocess_image(img: Image.Image, target_size=(224, 224)) -> np.ndarray:
    if img.size == (640, 480):
        img = img.rotate(90, expand=True)
    img = img.resize(target_size)
    arr = np.array(img).astype("float32") / 255.0
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    return np.expand_dims(arr, axis=0)


def predict_all(img: Image.Image):
    age_m, var_m, lbl_m = load_models()
    x = preprocess_image(img)

    age_norm = age_m.predict(x, verbose=0)[0][0]
    age_days = age_norm * (AGE_MAX - AGE_MIN) + AGE_MIN

    var_probs = var_m.predict(x, verbose=0)[0]
    var_idx = int(np.argmax(var_probs))
    VARIETIES = ['ADT45', 'AndraPonni', 'AtchayaPonni', 'IR20', 'KarnatakaPonni', 'Onthanel', 'Ponni', 'RR', 'Surya', 'Zonal']
    variety = VARIETIES[var_idx]

    lbl_probs = lbl_m.predict(x, verbose=0)[0]
    lbl_idx = int(np.argmax(lbl_probs))
    DISEASES = ['bacterial_leaf_blight', 'bacterial_leaf_streak', 'bacterial_panicle_blight', 'blast', 'brown_spot', 'dead_heart', 'downy_mildew', 'hispa', 'normal', 'tungro']
    label = DISEASES[lbl_idx]

    return float(age_days), variety, label
