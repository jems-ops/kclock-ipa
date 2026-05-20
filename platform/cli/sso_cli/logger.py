import logging

def setup_logger():
    logging.basicConfig(
        filename="sso-cli.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
