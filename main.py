from scrappers.one_time_scrapper import get_data_from_facebook_group_albums
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
    parser.add_argument('--excluded_albums',
                        type=str,
                        help='One time scrapper will scrap data from every album excluding albums from this group',
                        required=False)
    parser.add_argument('--included_albums',
                        type=str,
                        help='One time scrapper will scrap data from albums that are in this group (format: included_albums=[("Woj. Podlaskie", "117"),("Woj. Małopolskie", "124")])',
                        required=False)
    args = parser.parse_args()

    _type = args.type
    groups = args.groups.split(',')

    if _type == "periodic":
        for group in groups:
            get_data_from_group_board(group)
    elif _type == "one_time":
        excluded_albums = args.excluded_albums.split(',') if args.excluded_albums else []
        included_albums = args.included_albums.split(',') if args.included_albums else []
        for group in groups:
            get_data_from_facebook_group_albums(group, excluded_albums, included_albums)

if __name__ == '__main__':
    main()
