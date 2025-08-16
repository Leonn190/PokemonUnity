import random
from collections import deque, defaultdict
import Variaveis as V
import json
import math
import numpy as np
from sqlalchemy import Column, Text, Integer

class Mapa(V.db.Model):
    __tablename__ = "mapa"
    id = Column(Integer, primary_key=True)  # <-- ESSENCIAL
    biomas_json = Column(Text, nullable=False)
    objetos_json = Column(Text, nullable=False)

BIOME_ID = {
    "OCEAN":        0,
    "LAKE":         1,
    "PLAIN":        2,
    "FOREST":       3,
    "DESERT":       4,
    "SNOW":         5,
    "VULCANO":      6,
    "TERRA_MAGICA": 7,
    "PANTANO":      8,
}

def GerarMapa(W=1200, H=1200, SEED=random.randint(0,5000)):
    # ===================== Parâmetros principais / TUNING =====================
    random.seed(SEED)
    np.random.seed(SEED)

    # ---------- LAND vs OCEAN ----------
    SEA_LEVEL_BASE = 0.45
    LAND_MASS_BIAS = 0.00
    SEA_LEVEL = float(np.clip(SEA_LEVEL_BASE + LAND_MASS_BIAS, 0.02, 0.98))
    MOUNTAIN_LEVEL = 0.75

    # ====== LAGOS (controle por rate) ======
    LAKE_RATE = 0.45
    LAKE_MOISTURE_MIN = 0.70
    LAKE_MAX_ELEV = SEA_LEVEL + 0.08
    LAKE_SMOOTH_RADIUS = 1

    # ---- Tamanhos BASE e multiplicadores por BIOMA ----
    MIN_FRAC_SNOW   = 0.03
    MIN_FRAC_DESERT = 0.06
    MIN_FRAC_FOREST = 0.12

    SPECIAL_RATES_VOLCAN = 0.01
    SPECIAL_RATES_MAGIC  = 0.01
    SPECIAL_RATES_SWAMP  = 0.01

    SIZE_MULT = {
        "LAKE":         1.00,
        "SNOW":         1.00,
        "DESERT":       1.00,
        "FOREST":       1.00,
        "VULCANO":      1.00,
        "TERRA_MAGICA": 1.00,
        "PANTANO":      1.00,
    }

    # Critérios auxiliares dos especiais
    VOLCAN_MIN_COAST_DIST   = 6
    SWAMP_NEAR_LAKE_RADIUS  = 2
    SWAMP_NEAR_COAST_RADIUS = 3
    SWAMP_LOWLAND_MAX       = SEA_LEVEL + 0.06
    SWAMP_MOIST_MIN         = 0.60

    # Solidez dos especiais (morfologia)
    SPECIAL_SOLID_CLOSE_RADIUS = 2
    SPECIAL_SOLID_OPEN_RADIUS  = 0

    # ---- KNOBS dos biomas comuns ----
    TEMP_SNOW_MAX = 0.25
    MOIST_FOREST_MIN = 0.55
    MOIST_DESERT_MAX = 0.35
    TEMP_HOT_MIN = 0.65

    # --------- Limpeza de “manchinhas” ----------
    MIN_PATCH_SIZE_SNOW   = 1500
    MIN_PATCH_SIZE_DESERT = 1500

    # ===================== Utilidades de noise (FBM caseiro) =====================
    def value_noise(shape, cell=64, rng=np.random):
        h, w = shape
        gw = max(2, int(math.ceil(w / cell)) + 1)
        gh = max(2, int(math.ceil(h / cell)) + 1)
        grid = rng.rand(gh, gw)
        yy = np.linspace(0, gh - 1, h)
        xx = np.linspace(0, gw - 1, w)
        X, Y = np.meshgrid(xx, yy)
        x0 = np.floor(X).astype(int); y0 = np.floor(Y).astype(int)
        x1 = np.clip(x0 + 1, 0, gw - 1); y1 = np.clip(y0 + 1, 0, gh - 1)
        sx = X - x0; sy = Y - y0
        v00 = grid[y0, x0]; v10 = grid[y0, x1]
        v01 = grid[y1, x0]; v11 = grid[y1, x1]
        i1 = v00 * (1 - sx) + v10 * sx
        i2 = v01 * (1 - sx) + v11 * sx
        out = i1 * (1 - sy) + i2 * sy
        return out

    def fbm(shape, octaves=6, lacunarity=2.0, gain=0.5, base_cell=256, rng=np.random):
        h, w = shape
        total = np.zeros((h, w), dtype=np.float32)
        amp = 1.0
        freq_cell = base_cell
        for _ in range(octaves):
            n = value_noise((h, w), cell=max(4, int(freq_cell)), rng=rng)
            total += amp * n
            amp *= gain
            freq_cell /= lacunarity
        total -= total.min()
        total /= (total.max() + 1e-9)
        return total

    def normalize01(arr):
        arr = arr.astype(np.float32)
        arr -= arr.min()
        m = arr.max()
        if m > 0: arr /= m
        return arr

    # ===================== Gera campos base =====================
    def generate_elevation(shape):
        base = fbm(shape, octaves=7, lacunarity=2.1, gain=0.52, base_cell=220, rng=np.random)
        h, w = shape
        yy = np.linspace(-1, 1, h)
        xx = np.linspace(-1, 1, w)
        X, Y = np.meshgrid(xx, yy)
        r = np.sqrt(X*X + Y*Y)
        radial = np.clip(1.0 - r*0.9, 0.0, 1.0)  # centro mais alto, bordas mais baixas
        elev = 0.75*base + 0.25*radial
        return normalize01(elev)

    def generate_moisture(shape):
        return fbm(shape, octaves=5, lacunarity=2.0, gain=0.5, base_cell=300, rng=np.random)

    def generate_temperature(shape):
        h, w = shape
        lat = np.linspace(1.0, 0.0, h).reshape(h,1)  # topo frio
        noise = fbm(shape, octaves=4, lacunarity=2.0, gain=0.55, base_cell=260, rng=np.random)
        temp = 0.75*lat + 0.25*noise
        temp = normalize01(1.0 - temp)  # topo mais frio, base mais quente
        return temp

    def classify_relief(elev):
        relief = np.zeros_like(elev, dtype=np.uint8)
        relief[elev < SEA_LEVEL] = 0
        relief[(elev >= SEA_LEVEL) & (elev < MOUNTAIN_LEVEL)] = 1
        relief[elev >= MOUNTAIN_LEVEL] = 2
        return relief

    # ===================== Morfologia booleana =====================
    def dilate_bool(mask, radius=1):
        # garante booleano para o OR funcionar do jeito certo sem promover dtype
        mask = mask.astype(bool, copy=False)

        if radius <= 0:
            return mask.copy()

        h, w = mask.shape
        out = mask.copy()
        for dy in range(-radius, radius + 1):
            y0 = max(0,  dy); y1 = min(h,  h + dy)
            yy0 = max(0, -dy); yy1 = yy0 + (y1 - y0)
            if y1 - y0 <= 0:
                continue
            for dx in range(-radius, radius + 1):
                if dy == 0 and dx == 0:
                    continue
                x0 = max(0,  dx); x1 = min(w,  w + dx)
                xx0 = max(0, -dx); xx1 = xx0 + (x1 - x0)
                if x1 - x0 <= 0:
                    continue
                out[y0:y1, x0:x1] |= mask[yy0:yy1, xx0:xx1]
        return out

    def erode_bool(mask, radius=1):
        if radius <= 0: return mask.copy()
        return ~dilate_bool(~mask, radius)

    def close_bool(mask, radius=1):
        if radius <= 0: return mask.copy()
        return erode_bool(dilate_bool(mask, radius), radius)

    def open_bool(mask, radius=1):
        if radius <= 0: return mask.copy()
        return dilate_bool(erode_bool(mask, radius), radius)

    def fill_holes(mask: np.ndarray) -> np.ndarray:
        """
        Preenche buracos em 'mask' (True = sólido).
        Mesma lógica: flood-fill 4-conectado do complemento (~mask) a partir das bordas,
        depois retorna mask | holes. Implementação por SCANLINE (intervalos), que
        reduz drasticamente o uso de fila/memória. Resultado = idêntico ao BFS por pixel.
        """
        # Garante bool contíguo
        mask = np.ascontiguousarray(mask, dtype=bool)
        h, w = mask.shape
        if h == 0 or w == 0:
            return mask

        comp = ~mask                    # regiões "vazias" a serem analisadas
        outside = np.zeros_like(mask)   # marca o que é alcançável a partir da borda (fora dos buracos)

        q = deque()

        def push_span(y: int, x: int):
            """Expande horizontalmente a partir (y,x) sobre comp & ~outside, marca e enfileira [L,R)."""
            row_comp = comp[y]
            row_out  = outside[y]
            # anda pra esquerda
            L = x
            while L > 0 and row_comp[L-1] and not row_out[L-1]:
                L -= 1
            # anda pra direita
            R = x + 1
            while R < w and row_comp[R] and not row_out[R]:
                R += 1
            # marca o intervalo como outside e enfileira
            row_out[L:R] = True
            q.append((y, L, R))

        # ---- Semeadura nas bordas ----
        # Topo
        y = 0
        row_comp = comp[y]; row_out = outside[y]
        x = 0
        while x < w:
            if row_comp[x] and not row_out[x]:
                push_span(y, x)
                # pula direto o intervalo recém marcado
                while x < w and row_out[x]:
                    x += 1
            else:
                x += 1

        # Base
        y = h - 1
        row_comp = comp[y]; row_out = outside[y]
        x = 0
        while x < w:
            if row_comp[x] and not row_out[x]:
                push_span(y, x)
                while x < w and row_out[x]:
                    x += 1
            else:
                x += 1

        # Esquerda/Direita (garante atingir componentes que tocam só as colunas)
        for y in range(h):
            # esquerda
            if comp[y, 0] and not outside[y, 0]:
                push_span(y, 0)
            # direita
            if comp[y, w-1] and not outside[y, w-1]:
                push_span(y, w-1)

        # ---- Flood fill por intervalos ----
        while q:
            y, L, R = q.popleft()

            # linha de cima
            if y > 0:
                row_comp = comp[y-1]; row_out = outside[y-1]
                x = L
                # varre apenas a faixa [L, R) — suficiente para 4-conectividade
                while x < R:
                    if row_comp[x] and not row_out[x]:
                        push_span(y-1, x)
                        # avança até o fim do intervalo recém marcado
                        while x < w and row_out[x]:
                            x += 1
                    else:
                        x += 1

            # linha de baixo
            if y + 1 < h:
                row_comp = comp[y+1]; row_out = outside[y+1]
                x = L
                while x < R:
                    if row_comp[x] and not row_out[x]:
                        push_span(y+1, x)
                        while x < w and row_out[x]:
                            x += 1
                    else:
                        x += 1

        # holes = (~mask) & (~outside)  -> retorno = mask | holes
        return mask | (~outside)

    # ===================== Lagos =====================
    def place_lakes(elev, moisture):
        rate = float(np.clip(LAKE_RATE * SIZE_MULT.get("LAKE", 1.0), 0.0, 1.0))
        cand = (elev >= SEA_LEVEL) & (elev <= LAKE_MAX_ELEV) & (moisture >= LAKE_MOISTURE_MIN)
        if rate <= 0.0:
            lakes = np.zeros_like(elev, dtype=bool)
        elif rate >= 1.0:
            lakes = cand.copy()
        else:
            rnd = np.random.rand(*elev.shape)
            lakes = cand & (rnd < rate)
        if LAKE_SMOOTH_RADIUS > 0:
            lakes = close_bool(lakes, LAKE_SMOOTH_RADIUS)
            lakes = open_bool(lakes, 1)
        return lakes

    # ===================== Biomas comuns (numéricos) =====================
    def assign_biomes_base(elev, lakes, temp, moist):
        h, w = elev.shape
        biomes = np.full((h, w), BIOME_ID["PLAIN"], dtype=np.uint8)
        ocean = elev < SEA_LEVEL
        biomes[ocean] = BIOME_ID["OCEAN"]
        biomes[lakes & ~ocean] = BIOME_ID["LAKE"]
        land = ~ocean & ~lakes

        mask_snow = (temp <= TEMP_SNOW_MAX) & land
        biomes[mask_snow] = BIOME_ID["SNOW"]

        mask_desert = (temp >= TEMP_HOT_MIN) & (moist <= MOIST_DESERT_MAX) & land
        biomes[mask_desert] = BIOME_ID["DESERT"]

        mask_forest = (moist >= MOIST_FOREST_MIN) & land & ~mask_desert & ~mask_snow
        biomes[mask_forest] = BIOME_ID["FOREST"]
        return biomes

    # ===================== Enforce mínimos (numéricos) =====================
    def enforce_min_biomes(biomes, elev, temp, moist):
        out = biomes.copy()
        ocean = (out == BIOME_ID["OCEAN"])
        lakes = (out == BIOME_ID["LAKE"])
        land = ~ocean & ~lakes
        land_area = int(np.count_nonzero(land)) + 1

        targets = {
            BIOME_ID["SNOW"]:   int(np.clip(MIN_FRAC_SNOW   * SIZE_MULT["SNOW"],   0, 0.95) * land_area),
            BIOME_ID["DESERT"]: int(np.clip(MIN_FRAC_DESERT * SIZE_MULT["DESERT"], 0, 0.95) * land_area),
            BIOME_ID["FOREST"]: int(np.clip(MIN_FRAC_FOREST * SIZE_MULT["FOREST"], 0, 0.95) * land_area),
        }

        def expand_into_plain(target_id, base_cond, score, need):
            nonlocal out
            if need <= 0: return 0
            plain = (out == BIOME_ID["PLAIN"]) & land
            cand = plain & base_cond
            if not np.any(cand): return 0
            sc = score.copy(); sc[~cand] = -1e9
            take = min(need, int(np.count_nonzero(cand)))
            if take <= 0: return 0
            flat_idx = np.argpartition(sc.ravel(), -take)[-take:]
            yy, xx = np.unravel_index(flat_idx, sc.shape)
            sel = cand[yy, xx]
            out[yy[sel], xx[sel]] = target_id
            return int(sel.sum())

        counts = {k: int(np.count_nonzero(out == k)) for k in targets}
        for biome_id in (BIOME_ID["SNOW"], BIOME_ID["DESERT"], BIOME_ID["FOREST"]):
            need = targets[biome_id] - counts[biome_id]
            if need <= 0: continue

            if biome_id == BIOME_ID["SNOW"]:
                base = (temp <= (TEMP_SNOW_MAX + 0.08))
                score = (TEMP_SNOW_MAX + 0.08 - temp)
            elif biome_id == BIOME_ID["DESERT"]:
                base = (temp >= (TEMP_HOT_MIN - 0.08)) & (moist <= (MOIST_DESERT_MAX + 0.08))
                score = (temp - (moist*0.5))
            else:  # FOREST
                base = (moist >= (MOIST_FOREST_MIN - 0.08))
                score = moist

            need -= expand_into_plain(biome_id, base, score, need)
            if need > 0:
                if biome_id == BIOME_ID["SNOW"]:
                    base = (temp <= (TEMP_SNOW_MAX + 0.16))
                    score = (TEMP_SNOW_MAX + 0.16 - temp)
                elif biome_id == BIOME_ID["DESERT"]:
                    base = (temp >= (TEMP_HOT_MIN - 0.16)) & (moist <= (MOIST_DESERT_MAX + 0.16))
                    score = (temp - (moist*0.4))
                else:  # FOREST
                    base = (moist >= (MOIST_FOREST_MIN - 0.16))
                    score = moist
                expand_into_plain(biome_id, base, score, need)
        return out

    # ===================== Limpeza (snow/desert) numérica =====================
    def prune_small_patches(biomes):
        h, w = biomes.shape

        def process(target_id, min_size):
            visited = np.zeros((h, w), dtype=bool)
            mask = (biomes == target_id)
            for y in range(h):
                for x in range(w):
                    if not mask[y, x] or visited[y, x]:
                        continue
                    q = deque([(y, x)])
                    comp = []
                    visited[y, x] = True
                    border_neighbors = []
                    while q:
                        cy, cx = q.popleft()
                        comp.append((cy, cx))
                        for dy in (-1,0,1):
                            for dx in (-1,0,1):
                                if dy == 0 and dx == 0: continue
                                ny, nx = cy+dy, cx+dx
                                if 0 <= ny < h and 0 <= nx < w:
                                    if biomes[ny, nx] != target_id:
                                        border_neighbors.append(biomes[ny, nx])
                                    elif not visited[ny, nx]:
                                        visited[ny, nx] = True
                                        q.append((ny, nx))
                    if len(comp) < min_size:
                        counts = defaultdict(int)
                        for n in border_neighbors:
                            counts[int(n)] += 1
                        avoid = {BIOME_ID["OCEAN"], BIOME_ID["LAKE"], target_id}
                        best = None; bestc = -1
                        for k, v in counts.items():
                            if k in avoid: continue
                            if v > bestc:
                                best, bestc = k, v
                        if best is None:
                            best = BIOME_ID["PLAIN"]
                        for (cy, cx) in comp:
                            biomes[cy, cx] = best

        if MIN_PATCH_SIZE_SNOW > 0:
            process(BIOME_ID["SNOW"], MIN_PATCH_SIZE_SNOW)
        if MIN_PATCH_SIZE_DESERT > 0:
            process(BIOME_ID["DESERT"], MIN_PATCH_SIZE_DESERT)
        return biomes

    # ===================== Especiais (1 cada, sólidos) numéricos =====================
    def grow_blob_one_component(candidate_mask, target_area, rng, organic_field, avoid_mask=None, max_iter=10_000):
        h, w = candidate_mask.shape
        cand = candidate_mask.copy()
        if avoid_mask is not None:
            cand &= ~avoid_mask

        ys, xs = np.where(cand)
        if len(ys) == 0:
            return np.zeros_like(candidate_mask, dtype=bool)

        # seed inicial ponderada (igual à tua)
        vals = organic_field[ys, xs]
        probs = vals + 1e-6
        probs /= probs.sum()
        idx = rng.choice(len(ys), p=probs)
        sy, sx = int(ys[idx]), int(xs[idx])

        region = np.zeros_like(cand, dtype=bool)
        region[sy, sx] = True
        region_count = 1  # evita region.sum() a cada passo

        frontier = [(sy, sx)]           # lista simples
        visited = np.zeros((h, w), dtype=bool)
        visited[sy, sx] = True

        steps = 0
        while frontier and region_count < target_area and steps < max_iter:
            steps += 1

            # mesma lógica de escolha:
            # - se frontier > 8, pega o melhor entre uma amostra aleatória
            # - caso contrário, escolhe índice aleatório
            if len(frontier) > 8:
                sample_idx = rng.choice(len(frontier), size=min(8, len(frontier)), replace=False)
                best_i = int(sample_idx[0])
                best_v = -1.0
                for i in sample_idx:
                    y,x = frontier[int(i)]
                    v = organic_field[y, x]
                    if v > best_v:
                        best_v = v
                        best_i = int(i)
                pick_i = best_i
            else:
                pick_i = int(rng.integers(0, len(frontier)))

            # remove em O(1): swap-pop (em vez de pop(pick) que é O(n))
            y, x = frontier[pick_i]
            frontier[pick_i] = frontier[-1]
            frontier.pop()

            # expande vizinhos (mesma 8-conectividade e probabilidade)
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                        visited[ny, nx] = True
                        if not cand[ny, nx]:
                            continue
                        p = 0.55 + 0.4 * organic_field[ny, nx]
                        if rng.random() < p:
                            if not region[ny, nx]:
                                region[ny, nx] = True
                                region_count += 1
                                frontier.append((ny, nx))

        # solidificação (mesmas chamadas)
        if SPECIAL_SOLID_CLOSE_RADIUS > 0:
            region = close_bool(region, SPECIAL_SOLID_CLOSE_RADIUS)
        region = fill_holes(region)
        if SPECIAL_SOLID_OPEN_RADIUS > 0:
            region = open_bool(region, SPECIAL_SOLID_OPEN_RADIUS)
        return region

    def place_special_biomes(elev, relief, moist, biomes):
        h, w = elev.shape
        rng = np.random.default_rng(SEED + 1337)
        out = biomes.copy()

        ocean = elev < SEA_LEVEL
        land = ~ocean & (biomes != BIOME_ID["LAKE"])
        organic = fbm((h, w), octaves=5, lacunarity=2.0, gain=0.5, base_cell=180, rng=np.random)
        land_area = int(np.count_nonzero(land)) + 1
        far_from_ocean = ~dilate_bool(ocean, radius=VOLCAN_MIN_COAST_DIST)
        used = np.zeros((h, w), dtype=bool)

        def force_special(target_id, target_area):
            nonlocal out, used
            avail = land & (~used)
            avail_count = int(np.count_nonzero(avail))
            if avail_count == 0:
                avail = land.copy()
                avail_count = int(np.count_nonzero(avail))
                if avail_count == 0:
                    return
            take = max(1, min(target_area, avail_count))
            blob = grow_blob_one_component(avail, take, rng, organic, avoid_mask=None)
            out[blob] = target_id
            used |= blob

        # VULCANO
        volcan_target = max(1, int(SPECIAL_RATES_VOLCAN * SIZE_MULT["VULCANO"] * land_area))
        volcano_cand = (relief == 2) & land & far_from_ocean & (~used)
        volcano_blob = grow_blob_one_component(volcano_cand, volcan_target, rng, organic, avoid_mask=used)
        if volcano_blob.any():
            out[volcano_blob] = BIOME_ID["VULCANO"]; used |= volcano_blob
        else:
            cand_relax = (relief == 2) & land & (~used)
            volcano_blob = grow_blob_one_component(cand_relax, volcan_target, rng, organic, avoid_mask=used)
            if volcano_blob.any():
                out[volcano_blob] = BIOME_ID["VULCANO"]; used |= volcano_blob
            else:
                force_special(BIOME_ID["VULCANO"], volcan_target)

        # PANTANO
        swamp_target = max(1, int(SPECIAL_RATES_SWAMP * SIZE_MULT["PANTANO"] * land_area))
        lakes_mask = (out == BIOME_ID["LAKE"])
        near_lake = dilate_bool(lakes_mask, radius=SWAMP_NEAR_LAKE_RADIUS)
        swamp_cand = land & near_lake & (elev <= SWAMP_LOWLAND_MAX) & (moist >= SWAMP_MOIST_MIN) & (~used)
        swamp_blob = grow_blob_one_component(swamp_cand, swamp_target, rng, organic, avoid_mask=used)

        if not swamp_blob.any():
            near_coast = dilate_bool(ocean, radius=SWAMP_NEAR_COAST_RADIUS) & land
            swamp_cand2 = near_coast & (elev <= SWAMP_LOWLAND_MAX) & (moist >= SWAMP_MOIST_MIN) & (~used)
            swamp_blob = grow_blob_one_component(swamp_cand2, swamp_target, rng, organic, avoid_mask=used)

        if not swamp_blob.any():
            swamp_cand3 = land & (elev <= SWAMP_LOWLAND_MAX) & (moist >= (SWAMP_MOIST_MIN + 0.05)) & (~used)
            swamp_blob = grow_blob_one_component(swamp_cand3, swamp_target, rng, organic, avoid_mask=used)

        if not swamp_blob.any():
            swamp_cand4 = land & (moist >= (SWAMP_MOIST_MIN + 0.02)) & (~used)
            swamp_blob = grow_blob_one_component(swamp_cand4, swamp_target, rng, organic, avoid_mask=used)

        if swamp_blob.any():
            out[swamp_blob] = BIOME_ID["PANTANO"]; used |= swamp_blob
        else:
            force_special(BIOME_ID["PANTANO"], swamp_target)

        # TERRA MÁGICA
        magic_target = max(1, int(SPECIAL_RATES_MAGIC * SIZE_MULT["TERRA_MAGICA"] * land_area))
        not_extremes = land & (out != BIOME_ID["PANTANO"]) & (out != BIOME_ID["VULCANO"])
        magic_cand = not_extremes & (moist >= 0.58) & (elev >= SEA_LEVEL + 0.02) & (elev <= MOUNTAIN_LEVEL) & (~used)
        magic_blob = grow_blob_one_component(magic_cand, magic_target, rng, organic, avoid_mask=used)
        if magic_blob.any():
            out[magic_blob] = BIOME_ID["TERRA_MAGICA"]; used |= magic_blob
        else:
            magic_relax = land & (moist >= 0.55) & (~used)
            magic_blob = grow_blob_one_component(magic_relax, magic_target, rng, organic, avoid_mask=used)
            if magic_blob.any():
                out[magic_blob] = BIOME_ID["TERRA_MAGICA"]; used |= magic_blob
            else:
                force_special(BIOME_ID["TERRA_MAGICA"], magic_target)

        # sanity check final
        for target_id, target_area in [
            (BIOME_ID["VULCANO"], volcan_target),
            (BIOME_ID["PANTANO"], swamp_target),
            (BIOME_ID["TERRA_MAGICA"], magic_target),
        ]:
            if not np.any(out == target_id):
                force_special(target_id, target_area)

        return out

    # ===================== Pipeline =====================
    shape = (H, W)
    elev  = generate_elevation(shape)
    moist = generate_moisture(shape)
    temp  = generate_temperature(shape)

    relief = classify_relief(elev)
    lakes  = place_lakes(elev, moist)

    biomes = assign_biomes_base(elev, lakes, temp, moist)
    biomes = enforce_min_biomes(biomes, elev, temp, moist)
    biomes = prune_small_patches(biomes)
    biomes = place_special_biomes(elev, relief, moist, biomes)

    return biomes.astype(int).tolist()

OBJ_CONFIG = {
    0:  {"nome":"Árvore",       "spawn_rate":0.06,  "dist_min":5, "biomas":[2,7]},  # plain, vulcão, terra mágica
    1:  {"nome":"Palmeira",     "spawn_rate":0.06,  "dist_min":6, "biomas":[4]},      # deserto
    2:  {"nome":"Arvore2",      "spawn_rate":0.08,  "dist_min":4, "biomas":[3]},      # floresta
    3:  {"nome":"Pinheiro",     "spawn_rate":0.06,  "dist_min":4, "biomas":[5]},      # neve

    4:  {"nome":"Ouro",         "spawn_rate":0.004, "dist_min":5, "biomas":[2,3,5]},  # raros 4..8
    5:  {"nome":"Diamante",     "spawn_rate":0.003, "dist_min":5, "biomas":[5]},
    6:  {"nome":"Esmeralda",    "spawn_rate":0.003, "dist_min":5, "biomas":[4]},
    7:  {"nome":"Rubi",         "spawn_rate":0.003, "dist_min":5, "biomas":[6]},
    8:  {"nome":"Ametista",     "spawn_rate":0.003, "dist_min":5, "biomas":[7]},

    9:  {"nome":"Cobre",        "spawn_rate":0.01,  "dist_min":5, "biomas":[2,3,4,5,7]},
    10: {"nome":"Pedra",        "spawn_rate":0.05,  "dist_min":4, "biomas":[2,3,4,5,7]},
    11: {"nome":"Arbusto",      "spawn_rate":0.05,  "dist_min":3, "biomas":[2,3,4,5,7]},
    12: {"nome":"Poça de Lava", "spawn_rate":0.008, "dist_min":9, "biomas":[6]},
}

def GeraGridObjetos(grid_biomas, SEED=None, spawn_obj_rate=0.15):
    """
    Versão otimizada (CPU/memória) mantendo a lógica original:
    - sorteio global com mitigação A/K;
    - roleta por spawn_rate entre candidatos que passam distância;
    - distância euclidiana real; garantia de >=2 raros (4..8).
    """
    import numpy as np
    import math
    if SEED is not None:
        random.seed(SEED)
        np.random.seed(SEED ^ 0xA5A5A5A5)  # só para a máscara de tentativa; determinístico por SEED

    H = len(grid_biomas)
    W = len(grid_biomas[0]) if H else 0
    biome = np.asarray(grid_biomas, dtype=np.uint8, order="C")
    objetos = np.full((H, W), -1, dtype=np.int16)

    # --- radii únicos e pré-cálculo de "scanlines" (dy -> dx_max) para cada raio ---
    dist_unicas = sorted({int(cfg["dist_min"]) for cfg in OBJ_CONFIG.values()})
    dx_max_por_dy = {}
    for r in dist_unicas:
        dm2 = r * r
        linhas = []
        # há pontos válidos para |dy| <= r-1 (pois queremos dx^2 + dy^2 < r^2)
        for dy in range(-(r - 1), r):
            t = dm2 - dy * dy
            if t <= 0:
                continue
            dx_max = int(math.sqrt(t - 1e-9))
            if dx_max > 0:
                linhas.append((dy, dx_max))
        dx_max_por_dy[r] = linhas

    # mapas de proibição por raio: False=permitido, True=proibido
    forbid = {r: np.zeros((H, W), dtype=bool) for r in dist_unicas}

    def carimbar_todos_raios(y, x):
        # Marca como proibido, para TODOS os raios, o disco centrado em (y,x) com aquele raio
        for r in dist_unicas:
            linhas = dx_max_por_dy[r]
            for dy, dxm in linhas:
                yy = y + dy
                if 0 <= yy < H:
                    x0 = x - dxm
                    if x0 < 0: x0 = 0
                    x1 = x + dxm
                    if x1 >= W: x1 = W - 1
                    forbid[r][yy, x0:x1 + 1] = True

    # --- index por bioma: ids, pesos, raios (arrays pequenos; reusados por tile) ---
    by_biome = {}
    for b in range(0, 9):  # 0..8
        ids, pesos, raios = [], [], []
        for oid, cfg in OBJ_CONFIG.items():
            if b in cfg["biomas"]:
                ids.append(int(oid))
                pesos.append(float(cfg["spawn_rate"]))
                raios.append(int(cfg["dist_min"]))
        by_biome[b] = (ids, pesos, raios)  # listas (rápidas p/ loops curtos)

    # --- máscara de água para pular rápido ---
    agua = (biome == BIOME_ID["OCEAN"]) | (biome == BIOME_ID["LAKE"])

    # --- máscara de tentativa global (reduz 90% do trabalho quando 0.1) ---
    tentar = (np.random.random(size=(H, W)) < float(spawn_obj_rate))
    elegiveis = (~agua) & tentar
    pts = np.flatnonzero(elegiveis)
    # ordem natural já é boa; se quiser mais aleatório: rng.permutation(pts)

    # --- 1ª passada: tentativa por tile selecionado ---
    for idx in pts:
        y = int(idx // W)
        x = int(idx % W)
        if objetos[y, x] != -1:
            continue

        b = int(biome[y, x])
        ids, pesos, raios = by_biome[b]
        K = len(ids)
        if K == 0:
            continue

        # Conta quantos passam distância (A) e guarda candidatos aprovados
        aprov_ids, aprov_pesos, aprov_raios = [], [], []
        A = 0
        for i in range(K):
            r = raios[i]
            if not forbid[r][y, x]:
                aprov_ids.append(ids[i])
                aprov_pesos.append(pesos[i])
                aprov_raios.append(r)
                A += 1

        if A == 0:
            continue

        # mitigação A/K
        if random.random() >= (spawn_obj_rate * (A / K)):
            continue

        # roleta entre aprovados
        tot = sum(aprov_pesos)
        if tot <= 0.0:
            continue
        r = random.random() * tot
        acc = 0.0
        pick = 0
        for i, wgt in enumerate(aprov_pesos):
            acc += wgt
            if r <= acc:
                pick = i
                break

        oid = aprov_ids[pick]
        objetos[y, x] = oid
        carimbar_todos_raios(y, x)

    # --- 2ª passada: garantir >=2 de cada raro 4..8 ---
    raros = [4, 5, 6, 7, 8]
    for oid in raros:
        faltam = max(0, 2 - int((objetos == oid).sum()))
        if faltam <= 0:
            continue
        dist_min = int(OBJ_CONFIG[oid]["dist_min"])
        biomas_ok = set(OBJ_CONFIG[oid]["biomas"])

        tentativas = 1000
        while faltam > 0 and tentativas > 0:
            tentativas -= 1
            x = random.randint(0, W - 1)
            y = random.randint(0, H - 1)
            if objetos[y, x] != -1:
                continue
            if int(biome[y, x]) not in biomas_ok:
                continue
            if forbid[dist_min][y, x]:
                continue
            objetos[y, x] = oid
            carimbar_todos_raios(y, x)
            faltam -= 1
        # se acabar tentativas, aborta (como sua proteção original)

    return objetos.astype(int).tolist()

def gerar_e_salvar_mapa(largura, altura, seed=random.randint(0,5000)):
    # Gerar as grids
    grid_biomas = GerarMapa(largura, altura, SEED=seed)
    grid_objetos = GeraGridObjetos(grid_biomas, SEED=seed)

    # Serializar para JSON
    biomas_json = json.dumps(grid_biomas)
    objetos_json = json.dumps(grid_objetos)

    # Apaga todos os mapas existentes antes de salvar o novo
    V.db.session.query(Mapa).delete()

    # Cria o novo mapa
    novo_mapa = Mapa(biomas_json=biomas_json, objetos_json=objetos_json)
    V.db.session.add(novo_mapa)

    V.db.session.commit()
    