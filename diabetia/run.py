"""Lee hk_database.csv una sola vez y genera la Tabla 1 y el resumen para la Tabla 2."""

from process import load_data, process
from summary import write_summary
from table1 import write_table1


def main() -> None:
    df = process(load_data())
    write_table1(df)
    write_summary(df)


if __name__ == "__main__":
    main()
