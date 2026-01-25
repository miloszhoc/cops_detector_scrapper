from pathlib import Path


class ApiConnector:
    def __init__(self, api_context):
        super().__init__()
        self.api_context = api_context

    def download_image(self, url: str, destination_filepath: str):
        response = self.api_context.get(url)
        with open(destination_filepath, 'wb') as f:
            f.write(response.body())
        path_object = Path(destination_filepath)
        return path_object
