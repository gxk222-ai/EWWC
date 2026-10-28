"""Generate the dotted world map used on the Home and Global Presence pages.

Usage:
    python3 -I scripts/make_map.py <ne_110m_land.geojson> <ne_110m_admin_0_countries.geojson>

Source data: Natural Earth 1:110m (public domain), https://www.naturalearthdata.com
Writes templates/partials/world-map.svg. Re-run only if the map design changes.
"""
import json
import sys
from pathlib import Path

STEP = 2.0            # degrees between dots
K = 4.0               # pixels per degree (equirectangular)
LAT_TOP, LAT_BOTTOM = 78, -56
ATLANTA = (-84.388, 33.749)
SOUTH_AFRICA_LABEL = (24.0, -30.5)   # country label position, not a city


def project(lon, lat):
    return round((lon + 180) * K, 1), round((LAT_TOP - lat) * K, 1)


def rings_of(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def point_in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def build_index(features):
    polys = []
    for f in features:
        for poly in rings_of(f["geometry"]):
            outer = poly[0]
            xs = [p[0] for p in outer]
            ys = [p[1] for p in outer]
            polys.append(((min(xs), min(ys), max(xs), max(ys)), poly))
    return polys


def contains(polys, x, y):
    for (x0, y0, x1, y1), poly in polys:
        if x0 <= x <= x1 and y0 <= y <= y1 and point_in_ring(x, y, poly[0]):
            if not any(point_in_ring(x, y, hole) for hole in poly[1:]):
                return True
    return False


def main(land_path, countries_path):
    land = build_index(json.loads(Path(land_path).read_text())["features"])
    countries = json.loads(Path(countries_path).read_text())["features"]
    zaf = [f for f in countries if f["properties"].get("ADM0_A3") == "ZAF"]
    za = build_index(zaf)

    land_d, za_d = [], []
    lat = LAT_TOP - STEP / 2
    while lat > LAT_BOTTOM:
        lon = -180 + STEP / 2
        while lon < 180:
            if contains(land, lon, lat):
                x, y = project(lon, lat)
                (za_d if contains(za, lon, lat) else land_d).append(f"M{x} {y}h0")
            lon += STEP
        lat -= STEP

    w, h = project(180, LAT_BOTTOM)
    ax, ay = project(*ATLANTA)
    zx, zy = project(*SOUTH_AFRICA_LABEL)
    cx, cy = (ax + zx) / 2, min(ay, zy) - 120

    svg = f"""<svg class="world-map" viewBox="0 0 {w} {h}" role="img" aria-labelledby="map-title map-desc">
  <title id="map-title">Map of E Worldwide Consulting's delivery footprint</title>
  <desc id="map-desc">Atlanta, Georgia, United States, is the company's base. South Africa is highlighted as a key market for international projects.</desc>
  <path class="map-land" d="{''.join(land_d)}"/>
  <path class="map-za" d="{''.join(za_d)}"/>
  <path class="map-arc" d="M{ax} {ay}Q{cx:.1f} {cy:.1f} {zx} {zy}"/>
  <g class="map-marker" transform="translate({ax} {ay})" tabindex="0" aria-label="Atlanta, Georgia, United States">
    <circle class="map-pulse" r="14"/><circle class="map-dot" r="6"/>
    <text x="14" y="-12" class="map-label">Atlanta, GA</text>
  </g>
  <g class="map-marker" transform="translate({zx} {zy})" tabindex="0" aria-label="South Africa">
    <circle class="map-pulse" r="14"/><circle class="map-dot" r="6"/>
    <text x="14" y="-12" class="map-label">South Africa</text>
  </g>
</svg>
"""
    out = Path(__file__).resolve().parent.parent / "templates" / "partials" / "world-map.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"wrote {out} ({len(svg) // 1024} KB, {len(land_d) + len(za_d)} dots)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
