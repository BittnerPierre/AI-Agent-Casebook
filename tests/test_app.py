
def test_config_loading(config):
    assert config['Retrieval']['persist_directory'] == './data/chroma'