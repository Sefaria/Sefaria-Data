FROM docker.elastic.co/elasticsearch/elasticsearch:8.8.0
RUN bin/elasticsearch-plugin install --batch analysis-icu \
    https://github.com/Sefaria/Sefaria-ElasticSearch/releases/download/v1.1.6/sefaria-naive-lemmatizer-v1.1.6.zip \
    https://github.com/Sefaria/Sefaria-ElasticSearch/releases/download/v1.1.6/sefaria-naive-lemmatizer-less-prefixes-v1.1.6.zip
