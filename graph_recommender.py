import math
import networkx as nx
from typing import Optional

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1    = math.radians(lat1)
    phi2    = math.radians(lat2)
    d_phi   = math.radians(lat2 - lat1)
    d_lam   = math.radians(lon2 - lon1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

class AccessibilityGraph:

    def __init__(self):
        self.G = nx.Graph()
        self._built = False

    def build(self, places: list[dict]) -> None:
        self.G.clear()

        for p in places:
            self.G.add_node(
                p["id"],
                place_id  = p["id"],
                name      = p["name"],
                address   = p["address"],
                lat       = p["lat"],
                lon       = p["lon"],
                category  = p["category"],
                wheelchair= p.get("wheelchair", False),
                blind     = p.get("blind", False),
                deaf      = p.get("deaf", False),
                phone     = p.get("phone", "не указан"),
                chain_id  = p.get("chain_id"),
                notes     = p.get("notes", ""),
            )

        nodes_by_category: dict[str, list] = {}
        for node_id, data in self.G.nodes(data=True):
            cat = data["category"]
            nodes_by_category.setdefault(cat, []).append(node_id)

        for cat, node_ids in nodes_by_category.items():
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    u = node_ids[i]
                    v = node_ids[j]
                    u_data = self.G.nodes[u]
                    v_data = self.G.nodes[v]
                    dist = haversine(
                        u_data["lat"], u_data["lon"],
                        v_data["lat"], v_data["lon"]
                    )
                    self.G.add_edge(u, v, weight=dist)

        self._built = True

    def find_nearest_adapted(
        self,
        user_lat: float,
        user_lon: float,
        category: str,
        nosology: str,
        limit: int = 3,
        exclude_id: Optional[int] = None,
    ) -> list[dict]:
        if not self._built:
            return []

        candidates = []
        for node_id, data in self.G.nodes(data=True):
            if data["category"] != category:
                continue
            if exclude_id and node_id == exclude_id:
                continue
            if not data.get(nosology, False):
                continue

            dist = haversine(user_lat, user_lon, data["lat"], data["lon"])
            candidates.append({
                "id":          node_id,
                "name":        data["name"],
                "address":     data["address"],
                "lat":         data["lat"],
                "lon":         data["lon"],
                "phone":       data["phone"],
                "category":    data["category"],
                "chain_id":    data["chain_id"],
                "wheelchair":  data["wheelchair"],
                "blind":       data["blind"],
                "deaf":        data["deaf"],
                "notes":       data["notes"],
                "distance_km": dist,
            })

        candidates.sort(key=lambda x: x["distance_km"])
        return candidates[:limit]

    def find_nearest_same_chain(
        self,
        user_lat: float,
        user_lon: float,
        chain_id: int,
        nosology: str,
        limit: int = 3,
        exclude_id: Optional[int] = None,
    ) -> list[dict]:
        if not self._built:
            return []

        candidates = []
        for node_id, data in self.G.nodes(data=True):
            if data.get("chain_id") != chain_id:
                continue
            if exclude_id and node_id == exclude_id:
                continue
            if not data.get(nosology, False):
                continue

            dist = haversine(user_lat, user_lon, data["lat"], data["lon"])
            candidates.append({
                "id":          node_id,
                "name":        data["name"],
                "address":     data["address"],
                "lat":         data["lat"],
                "lon":         data["lon"],
                "phone":       data["phone"],
                "category":    data["category"],
                "chain_id":    data["chain_id"],
                "wheelchair":  data["wheelchair"],
                "blind":       data["blind"],
                "deaf":        data["deaf"],
                "notes":       data["notes"],
                "distance_km": dist,
            })

        candidates.sort(key=lambda x: x["distance_km"])
        return candidates[:limit]

    def get_stats(self) -> dict:
        return {
            "vertices":   self.G.number_of_nodes(),
            "edges":      self.G.number_of_edges(),
            "categories": len(set(
                data["category"]
                for _, data in self.G.nodes(data=True)
            )),
        }

accessibility_graph = AccessibilityGraph()

async def build_graph_from_db(session) -> None:
    from sqlalchemy import select
    from db.models import Place, Accessibility, Chain

    result = await session.execute(
        select(Place, Accessibility, Chain)
        .join(Accessibility, Place.id == Accessibility.place_id)
        .outerjoin(Chain, Place.chain_id == Chain.id)
    )
    rows = result.all()

    places = []
    for place, acc, chain in rows:
        places.append({
            "id":          place.id,
            "name":        place.name,
            "address":     place.address,
            "lat":         place.lat,
            "lon":         place.lon,
            "phone":       place.phone or "не указан",
            "category":    place.category.value if place.category else "",
            "chain_id":    place.chain_id,
            "wheelchair":  acc.wheelchair,
            "blind":       acc.blind,
            "deaf":        acc.deaf,
            "notes":       acc.notes or "",
        })

    accessibility_graph.build(places)
    stats = accessibility_graph.get_stats()
    print(f"  Граф построен: |V|={stats['vertices']} вершин, "
          f"|E|={stats['edges']} рёбер, "
          f"{stats['categories']} категорий")
