from setuptools import setup

setup(
    name='prodigy_utils',
    entry_points={
        'prodigy_recipes': [
            'ref-tagging-recipe = recipes:ref_tagging_recipe'
        ],
        'prodigy_db': [
            'mongodb = db_manager:db_manager'
        ]
    },
    install_requires=[
        'prodigy>=1.10.0',
        'pymongo',
        'spacy>=3.0.0',
        'srsly'
    ]
)