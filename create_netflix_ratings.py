"""Create a flat Netflix ratings CSV from the Kaggle Prize dataset."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import kagglehub


def parse_ratings(file_path: Path, writer: csv.writer) -> int:
    current_movie_id: int | None = None
    rating_count = 0

    with file_path.open("r", encoding="latin-1") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            if line.endswith(":"):
                current_movie_id = int(line[:-1])
                continue

            if current_movie_id is None:
                raise ValueError(f"Rating before movie ID at line {line_number}")

            fields = line.split(",")
            if len(fields) != 3:
                raise ValueError(f"Invalid rating at line {line_number}: {line}")

            user_id, rating, date = fields
            rating_value = int(rating)
            if not 1 <= rating_value <= 5:
                raise ValueError(f"Rating outside 1-5 at line {line_number}")

            writer.writerow([current_movie_id, int(user_id), rating_value, date])
            rating_count += 1

    return rating_count


def create_ratings_csv(output_path: Path, force: bool = False) -> int:
    if output_path.exists() and output_path.stat().st_size > 0 and not force:
        print(f"Using existing file: {output_path}")
        return -1

    dataset_path = Path(kagglehub.dataset_download("netflix-inc/netflix-prize-data"))
    rating_files = sorted(dataset_path.glob("combined_data_*.txt"))
    if len(rating_files) != 4:
        raise FileNotFoundError(
            f"Expected four combined rating files in {dataset_path}, found {len(rating_files)}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    total_ratings = 0

    try:
        with temporary_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.writer(output_file)
            writer.writerow(["movie_id", "user_id", "rating", "date"])

            for rating_file in rating_files:
                print(f"Processing {rating_file.name}")
                total_ratings += parse_ratings(rating_file, writer)

        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    print(f"Created {output_path} with {total_ratings:,} ratings")
    return total_ratings


def create_movie_titles_csv(dataset_path: Path, output_path: Path, force: bool = False) -> None:
    source_path = dataset_path / "movie_titles.csv"
    if not source_path.exists():
        raise FileNotFoundError(f"Movie title file not found: {source_path}")
    if output_path.exists() and output_path.stat().st_size > 0 and not force:
        print(f"Using existing file: {output_path}")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        shutil.copyfile(source_path, temporary_path)
        temporary_path.replace(output_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    print(f"Created {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/netflix_ratings.csv"),
        help="Output CSV path (default: data/netflix_ratings.csv)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recreate the CSV even when a non-empty output already exists",
    )
    args = parser.parse_args()
    dataset_path = Path(kagglehub.dataset_download("netflix-inc/netflix-prize-data"))
    create_movie_titles_csv(
        dataset_path,
        args.output.parent / "movie_titles.csv",
        force=args.force,
    )
    create_ratings_csv(args.output, force=args.force)


if __name__ == "__main__":
    main()
