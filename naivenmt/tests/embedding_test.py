# Copyright 2018 luozhouyang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import tensorflow as tf

from naivenmt.configs import HParamsBuilder
from naivenmt.embeddings import Embedding
from naivenmt.tests import common_test_utils as common_utils
from naivenmt.utils import dataset_utils

TEST_DATA_DIR = common_utils.get_testdata_dir()


class EmbeddingTest(tf.test.TestCase):

  def testCreateEmbedding(self):
    self.hparams = HParamsBuilder().build()

    print("Source vocab size: %d" % self.hparams.source_vocab_size)
    print("Target vocab size: %d" % self.hparams.target_vocab_size)
    self.assertEqual(100, self.hparams.source_vocab_size)
    self.assertEqual(100, self.hparams.target_vocab_size)

    embedding = Embedding(src_vocab_size=self.hparams.source_vocab_size,
                          tgt_vocab_size=self.hparams.target_vocab_size,
                          src_vocab_file=self.hparams.source_vocab_file,
                          tgt_vocab_file=self.hparams.target_vocab_file,
                          share_vocab=False,
                          src_embedding_size=16,
                          tgt_embedding_size=16)

    with self.test_session() as sess:
      sess.run(tf.tables_initializer())
      sess.run(tf.global_variables_initializer())

      encoder_input = embedding.encoder_embedding_input(
        tf.constant([['<unk>', '<s>']]))
      self.assertEqual(1, sess.run(tf.shape(encoder_input))[0])  # batch size
      self.assertEqual(2, sess.run(tf.shape(encoder_input))[1])  # time steps
      self.assertEqual(16, sess.run(tf.shape(encoder_input))[2])  # embed size
      print(sess.run(encoder_input))

      decoder_input = embedding.decoder_embedding_input(
        tf.constant([['<unk>', '<s>', '</s>']]))
      self.assertEqual(1, sess.run(tf.shape(decoder_input))[0])
      self.assertEqual(16, sess.run(tf.shape(decoder_input))[2])
      print(sess.run(decoder_input))

  def testLoadFromFile(self):
    configs = {
      "embed_prefix": common_utils.get_testdata_file("test_embed"),
      "vocab_prefix": common_utils.get_testdata_file("test_embed_vocab")
    }
    hparams = HParamsBuilder(configs).build()

    self.assertEqual(6, hparams.source_vocab_size)
    self.assertEqual(6, hparams.target_vocab_size)

    embedding = Embedding(src_vocab_size=hparams.source_vocab_size,
                          tgt_vocab_size=hparams.target_vocab_size,
                          src_vocab_file=hparams.source_vocab_file,
                          tgt_vocab_file=hparams.target_vocab_file,
                          src_embedding_file=hparams.source_embed_file,
                          tgt_embedding_file=hparams.target_embed_file,
                          share_vocab=False,
                          src_embedding_size=4,
                          tgt_embedding_size=4)
    with self.test_session() as sess:
      sess.run(tf.tables_initializer())
      sess.run(tf.global_variables_initializer())

      # embedding of 'The' and 'behind'
      encoder_input = embedding.encoder_embedding_input(
        tf.constant([[b'The', '</s>'], ['The', 'behind']]))
      print(sess.run(tf.shape(encoder_input)))
      self.assertEqual(2, sess.run(tf.shape(encoder_input))[0])  # batch size
      self.assertEqual(2, sess.run(tf.shape(encoder_input))[1])  # time steps
      self.assertEqual(4, sess.run(tf.shape(encoder_input))[2])  # embed size
      encoder_input = sess.run(encoder_input)
      the = sess.run(tf.constant([1.5, 2.5, 3.5, 4.5], dtype=tf.float32))
      behind = sess.run(tf.constant([2.4, 3.4, 4.4, 5.4], dtype=tf.float32))
      self.assertAllEqual(the, encoder_input[0][0])
      self.assertAllEqual(behind, encoder_input[1][1])

      decoder_input = embedding.decoder_embedding_input(
        tf.constant([['Khoa', 'học', 'sau']]))
      self.assertEqual(1, sess.run(tf.shape(decoder_input))[0])
      self.assertEqual(3, sess.run(tf.shape(decoder_input))[1])
      self.assertEqual(4, sess.run(tf.shape(decoder_input))[2])
      decoder_input = sess.run(decoder_input)
      khoa = sess.run(tf.constant([1.3, 2.3, 3.3, 4.3], dtype=tf.float32))
      hoc = sess.run(tf.constant([1.2, 2.2, 3.3, 4.3], dtype=tf.float32))
      sau = sess.run(tf.constant([1.1, 2.1, 3.1, 4.1], dtype=tf.float32))
      self.assertAllEqual(khoa, decoder_input[0][0])
      self.assertAllEqual(hoc, decoder_input[0][1])
      self.assertAllEqual(sau, decoder_input[0][2])

  def testEmbeddingEncoderInput(self):
    configs = {
      "embed_prefix": common_utils.get_testdata_file("test_embed"),
      "vocab_prefix": common_utils.get_testdata_file("test_embed_vocab"),
      "random_seed": 1000,
      "num_buckets": 5,
      "src_max_len": 50,
      "tgt_max_len": 50,
      "num_parallel_calls": 4,
      "buff_size": 1024,
      "skip_count": 0,
      "batch_size": 4,
      "source_embedding_size": 4,
      "target_embedding_size": 4
    }
    hparams = HParamsBuilder(configs).build()
    embedding = Embedding(src_vocab_size=hparams.source_vocab_size,
                          tgt_vocab_size=hparams.target_vocab_size,
                          src_vocab_file=hparams.source_vocab_file,
                          tgt_vocab_file=hparams.target_vocab_file,
                          share_vocab=False,
                          src_embedding_size=hparams.source_embedding_size,
                          tgt_embedding_size=hparams.target_embedding_size)

    features, labels = dataset_utils.build_dataset(
      hparams,
      tf.estimator.ModeKeys.TRAIN)
    features_embedding = embedding.encoder_embedding_input(features['inputs'])
    with self.test_session() as sess:
      sess.run(tf.global_variables_initializer())
      sess.run(tf.tables_initializer())
      print(sess.run(features_embedding))
      self.assertEqual(3, sess.run(tf.rank(features_embedding)))
      self.assertEqual(hparams.batch_size,
                       sess.run(tf.shape(features_embedding))[0])
      self.assertEqual(hparams.source_embedding_size,
                       sess.run(tf.shape(features_embedding))[2])


if __name__ == "__main__":
  tf.test.main()
