#!/usr/bin/env python
import sys
from src.scripts.IchnosCF import main as carbon_main
from src.scripts.Convertor import convert as convert


def main(command, arguments):
    match command:
        case "calculate-emissions":
            carbon_main(arguments)
        case "convert":
            convert(arguments)



if __name__ == "__main__":
    args: list[str] = sys.argv
    assert len(args) >= 2
    main(sys.argv[1], sys.argv[2:])
