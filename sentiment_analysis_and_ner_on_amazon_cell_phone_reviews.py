# -*- coding: utf-8 -*-
"""Sentiment_Analysis_and_NER_on_Amazon_Cell_Phone_Reviews

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1LEMRXVNPwOCu1oMO-iG64t-OtS1jsr2V

# **NER AND SENTIMENT ANALYSIS ON AMAZON CELL PHONE REVIEWS**

## Library Imports and Dataset Loading
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import string
import re
import nltk
import warnings
warnings.filterwarnings('ignore')
import seaborn as sns
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer 
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_datasets as tfds
from tensorflow import keras
from sklearn.utils.class_weight import compute_class_weight
import os
from keras.callbacks import Callback
from keras import regularizers
import matplotlib.pyplot as plt
import numpy as np
from scikitplot.metrics import plot_confusion_matrix, plot_roc

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('averaged_perceptron_tagger')

pip install scikit-plot

df = pd.read_csv("/content/20191226-reviews.csv")

df.info()

#Taking a subset of the data with only required columns
df = df[['rating', 'body']]

df.info()

#Dropping all null values 
df = df.dropna()

"""## **Named Entity Recognition**"""

#function to get only ORGANIZATIONS detected from NER (to obtain brands)
def get_NER_org(x):
  ner_orgs = []
  doc = nlp(x)
  for ent in doc.ents:
      if (ent.label_ == 'ORG'):
        ner_orgs.append(ent.text.lower())
  return list(set(ner_orgs))

#Loading the English language spacy model for NER
nlp = en_core_web_sm.load()

#Applying the ORG filter function on the dataset
df['NER_brands'] = df.apply(lambda x: get_NER_org(x.body), axis=1)

#Calculating number of ORG detected for each row
df['NER_brand_count'] = df.apply(lambda x: len(x.NER_brands), axis=1)

df['NER_brands'][1345]

print(len(df['NER_brands'][1345]))

#Filtering dataset to obtain records with only one NER ORG detected for future studies
df = df[(df.NER_brand_count == 1)]

df.reset_index(inplace=True)

#Exporting value counts as csv to see entire list of NER ORG detected
(df.NER_brands.value_counts()).to_csv('name.csv')

df['NER_brands'] = df['NER_brands'].apply(lambda x: ','.join(map(str, x)))

df['NER_brands'][185]

df['body'][185]

#creating a subset of the data
data_final = df

#combining apple and iphones as one brand
data_final['NER_brands'] = data_final['NER_brands'].replace(['iphones'],'apple')

#filtering the dataset to obtain only some of the leading cell phone brands
brand_list = ["samsung", "android", "nokia", "sony", "apple", "huawei", "xiaomi"]
data_final = data_final[data_final['NER_brands'].isin(brand_list)]

data_final.NER_brands.value_counts()

#Visualize the brand distribution as detected by NER
colors = sns.color_palette('pastel')[0:5] #define Seaborn color palette to use
plt.figure(figsize=(7,7))
plt.pie(data_final['NER_brands'].value_counts(), labels = data_final['NER_brands'].value_counts().index, colors = colors, autopct='%.0f%%')
plt.title("NER Brand Distribution")
plt.show()

"""## Data Pre-processing for NLP"""

#function to remove unwanted characters and convert all text to lower case
def clean_text(text):
    text = str(text).lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    return text

#function to remove emoticons, foreign characters and symbols
def remove_emoji(string):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)

#function to obtain the part-of-speech of words in the text
def get_wordnet_pos(word):
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.VERB)

#function to lemmatize, remove stop words and tokenize the text
def lemmatize_text(description_):
    individual_word_list=[]
    lemmatizer = WordNetLemmatizer() 
    words = word_tokenize(description_)
    stop_words = stopwords.words('english')

    words_without_sw = [word for word in words if not word in stop_words]

    for word in words_without_sw:
      individual_word_list.append(lemmatizer.lemmatize(word, get_wordnet_pos(word)))
           
    return ' '.join(individual_word_list)

#apply the cleaning functions on the reviews text in the dataframe
data_final["body_cleaned"] = data_final["body"].apply(lambda x:clean_text(str(x)))
data_final["body_cleaned"] = data_final["body_cleaned"].apply(lambda x:remove_emoji(str(x)))
data_final['body_cleaned'] = data_final['body_cleaned'].apply(lemmatize_text)

#sample text after cleaning
data_final['body_cleaned'][0]

"""### Checking for data imbalance"""

data_final.rating.value_counts()

#Visualizing the distribution of the ratings
plt.figure(figsize=(5,5))
sns.countplot(data_final['rating'])
plt.show()

#Encoding the rating to a scale from 0 to 4 (required to apply class_weights from scikit to balance data) 
replace_dict = {1:0, 2:1, 3:2, 4:3, 5:4 }
data_final=data_final.replace({"rating": replace_dict})

"""### Splitting Dataset into Training , Validation and Testing"""

# Shuffle your dataset 
shuffle_df = data_final.sample(frac=1)

# Define a size for your train, val and test sets (70:10:20 respectively)
train_size = int(0.7* len(data_final))
val_size = int(0.1* len(data_final))
test_size = int(0.2* len(data_final))

# Split your dataset 
train_df = shuffle_df[:train_size]
val_df = shuffle_df[train_size:(train_size+val_size)]
test_df = shuffle_df[(train_size+val_size) : ]

print(train_df.shape)
print(test_df.shape)
print(val_df.shape)

#Converting the respective feature and target columns to arrays
X_train = train_df['body_cleaned'].to_numpy()
y_train = train_df['rating'].to_numpy()
X_val = val_df['body_cleaned'].to_numpy()
y_val = val_df['rating'].to_numpy()
X_test = test_df['body_cleaned'].to_numpy()
y_test = test_df['rating'].to_numpy()

X_train

"""## Model Building

### Simple Tensorflow and Keras model with basic embedding
"""

#Embedding using Google Universal Sentence Encoder
embedding = "https://tfhub.dev/google/universal-sentence-encoder/4"

#Creating the hub layer with the embedded data
hub_layer = hub.KerasLayer(embedding, input_shape=[], dtype=tf.string, trainable=True)

#Defining the model architecture (layers)

model = keras.Sequential()
model.add(hub_layer) #embedding layer
model.add(keras.layers.Dense(16, kernel_regularizer=regularizers.l2(0.001), activation='relu'))
model.add(keras.layers.Dropout(0.5))
model.add(keras.layers.Dense(8, kernel_regularizer=regularizers.l2(0.001), activation='relu'))
model.add(keras.layers.Dropout(0.5))
model.add(keras.layers.Dense(5, activation='softmax'))

model.summary()

#Compiling the model
#Optimizer - Adam
#Loss function - SparseCategoricalCrossentropy
#Metric - Accuracy
model.compile(optimizer='Adam', loss=keras.losses.SparseCategoricalCrossentropy(from_logits=False),metrics=['Accuracy'])

#Funtion to output a confusion matrix on validation data at each epoch
class PerformanceVisualizationCallback(Callback):    
    def __init__(self, model, validation_data, image_dir):
        super().__init__()
        self.model = model
        self.validation_data = validation_data
        
        os.makedirs(image_dir, exist_ok=True)
        self.image_dir = image_dir

    def on_epoch_end(self, epoch, logs={}):
        y_pred = np.asarray(self.model.predict(self.validation_data[0]))
        y_true = self.validation_data[1]             
        y_pred_class = np.argmax(y_pred, axis=1)

        # plot and save confusion matrix
        fig, ax = plt.subplots(figsize=(16,12))
        plot_confusion_matrix(y_true, y_pred_class, ax=ax)
        fig.savefig(os.path.join(self.image_dir, f'confusion_matrix_epoch_{epoch}'))

#Setting up the performance visualization functions
performance_cbk = PerformanceVisualizationCallback(
                      model=model,
                      validation_data=(X_val, y_val),
                      image_dir='performance_vizualizations')

#Balancing the data imbalance
class_weights = compute_class_weight(
                                        class_weight = "balanced",
                                        classes = np.unique(y_train),
                                        y = y_train                                                    
                                    )
class_weights = dict(zip(np.unique(y_train), class_weights))
class_weights

#Introducing Early Stopping to prevent overfitting
callback = tf.keras.callbacks.EarlyStopping(monitor='loss', patience=3)

#Fitting the model
history = model.fit(X_train, y_train, batch_size=32, class_weight = class_weights, epochs=20,callbacks=[callback, performance_cbk],validation_data =(X_val, y_val), verbose=1)

#Evaluating the model with the test set
results = model.evaluate(X_test, y_test)

"""## Point of Data Testing (Unit Testing)"""

def get_rating(text):
  out=(model.predict([text])).argmax()
  print(model.predict([text]))
  if out==0:
    print("1 star")
  elif out==1:
    print("2 star")
  elif out==2:
    print("3 star")
  elif out==3:
    print("4 star")
  elif out==4:
    print("5 star")

get_rating("Excellent phone")

get_rating("The phone is ok")

get_rating("The phone is terrible and I hated every bit of it")