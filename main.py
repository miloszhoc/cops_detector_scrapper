from utils.logs import LOGGER
import argparse

from scrappers.periodic_scrapper import get_data_from_group_board


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type",
                        type=str,
                        required=True,
                        help="Type: periodic or one_time",
                        choices=["periodic", "one_time"])
    parser.add_argument('--groups',
                        type=str,
                        help='Coma separated list of groups',
                        required=True)
    args = parser.parse_args()

    _type = args.type
    groups = args.groups.split(',')

    for group in groups:
        get_data_from_group_board(group)


if __name__ == '__main__':
    main()
