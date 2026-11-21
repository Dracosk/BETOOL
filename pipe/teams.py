import argparse
import asyncio
from pathlib import Path
import pandas as pd
from pipe.cleaning import normalize_team_name
from pipe.data import clean_seasons, open_tab, parse_url, tab_teams
from utils.s3_tool import upload_to_s3

leagues = {
    'Premier League': 'https://www.sofascore.com/es/football/tournament/england/premier-league/17',
    'La Liga': 'https://www.sofascore.com/es/football/tournament/spain/laliga/8',
    'Bundesliga': 'https://www.sofascore.com/es/football/tournament/germany/bundesliga/35',
    'Serie A': 'https://www.sofascore.com/es/football/tournament/italy/serie-a/23',
    'Ligue 1': 'https://www.sofascore.com/es/football/tournament/france/ligue-1/34',
    'Eredivisie': 'https://www.sofascore.com/es/football/tournament/netherlands/eredivisie/37',
    'Belgium Pro League': 'https://www.sofascore.com/es/football/tournament/belgium/pro-league/38',
    'Championship': 'https://www.sofascore.com/es/football/tournament/england/championship/18'
}

S3_PREFIX = "processed/sofascore/teams"


async def main(upload=False):
    run_id = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d_%H-%M-%S_%f")
    catalog_parts = []
    failed_leagues = []

    for league_name, url in leagues.items():
        try:
            league_id, season_id = parse_url(url)
            async with open_tab(url) as tab:
                if season_id is None:
                    seasons = await clean_seasons(tab, league_id)
                    if not seasons or not seasons[0]["season_id"]:
                        raise ValueError("No season ID found.")
                    season_id = seasons[0]["season_id"]

                teams = await tab_teams(tab, league_id=league_id, season_id=season_id)

            if not teams:
                raise ValueError("No teams found.")

            catalog = pd.DataFrame(teams).rename(columns={"team_name": "team_name_original"})
            catalog["team_id"] = pd.to_numeric(catalog["team_id"], errors="raise").astype("int64")
            catalog["team_name_original"] = catalog["team_name_original"].astype("string")
            catalog["team_name"] = catalog["team_name_original"].map(normalize_team_name).astype("string")
            catalog["league_id"] = int(league_id)
            catalog["season_id"] = int(season_id)
            if catalog["team_name"].eq("").any() or catalog["team_name"].duplicated().any():
                raise ValueError("Empty or ambiguous normalized team names.")

            catalog_parts.append(catalog)
            print(f"{league_name} | season {season_id} | {len(catalog)} teams", flush=True)
        except Exception as exc:
            failed_leagues.append(league_name)
            print(f"Error processing {league_name}: {exc}", flush=True)

    if failed_leagues:
        print(f"Catalog incomplete. Failed leagues: {', '.join(failed_leagues)}", flush=True)
        return 1

    catalog = pd.concat(catalog_parts, ignore_index=True)
    catalog = catalog[["team_id", "team_name", "team_name_original", "league_id", "season_id"]]
    output_path = Path("data") / "teams_check" / run_id / "teams.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=False)
    catalog.to_parquet(output_path, index=False)
    print(f"Saved {len(catalog)} teams to {output_path}", flush=True)

    if upload:
        s3_key = upload_to_s3(S3_PREFIX, output_path)
        if s3_key is False:
            return 1
        print(f"Published catalog: {s3_key}", flush=True)

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", action="store_true", help="Publish the catalog to S3.")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(upload=args.upload)))
