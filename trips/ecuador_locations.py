"""
Provincias, capitales, terminales, zonas turísticas y playas del Ecuador con coordenadas.
Utilizado por OSRM para calcular distancias y tiempos de viaje.
"""

ECUADOR_LOCATIONS = [
    # --- Capitales de provincia ---
    {"city": "Quito", "province": "Pichincha", "lat": -0.1807, "lon": -78.4678},
    {"city": "Guayaquil", "province": "Guayas", "lat": -2.1962, "lon": -79.8862},
    {"city": "Cuenca", "province": "Azuay", "lat": -2.9006, "lon": -79.0045},
    {"city": "Ambato", "province": "Tungurahua", "lat": -1.2491, "lon": -78.6168},
    {"city": "Manta", "province": "Manabí", "lat": -0.9621, "lon": -80.7127},
    {"city": "Santo Domingo", "province": "Santo Domingo de los Tsáchilas", "lat": -0.2542, "lon": -79.1753},
    {"city": "Loja", "province": "Loja", "lat": -3.9931, "lon": -79.2042},
    {"city": "Machala", "province": "El Oro", "lat": -3.2586, "lon": -79.9553},
    {"city": "Portoviejo", "province": "Manabí", "lat": -1.0546, "lon": -80.4545},
    {"city": "Esmeraldas", "province": "Esmeraldas", "lat": 0.9592, "lon": -79.6540},
    {"city": "Riobamba", "province": "Chimborazo", "lat": -1.6709, "lon": -78.6546},
    {"city": "Ibarra", "province": "Imbabura", "lat": 0.3514, "lon": -78.1222},
    {"city": "Latacunga", "province": "Cotopaxi", "lat": -0.9353, "lon": -78.6155},
    {"city": "Babahoyo", "province": "Los Ríos", "lat": -1.8019, "lon": -79.5343},
    {"city": "Tulcán", "province": "Carchi", "lat": 0.8117, "lon": -77.7163},
    {"city": "Puyo", "province": "Pastaza", "lat": -1.4857, "lon": -78.0027},
    {"city": "Tena", "province": "Napo", "lat": -0.9890, "lon": -77.8155},
    {"city": "Macas", "province": "Morona Santiago", "lat": -2.3087, "lon": -78.1118},
    {"city": "Zamora", "province": "Zamora Chinchipe", "lat": -4.0692, "lon": -78.9567},
    {"city": "Azogues", "province": "Cañar", "lat": -2.7398, "lon": -78.8486},
    {"city": "Guaranda", "province": "Bolívar", "lat": -1.5925, "lon": -79.0008},
    {"city": "Nueva Loja", "province": "Sucumbíos", "lat": 0.0852, "lon": -76.8953},
    {"city": "Puerto Francisco de Orellana", "province": "Orellana", "lat": -0.4671, "lon": -76.9871},
    {"city": "Santa Elena", "province": "Santa Elena", "lat": -2.2262, "lon": -80.8587},

    # --- Terminales ---
    {"city": "Carcelén (Quito)", "province": "Pichincha", "lat": -0.1120, "lon": -78.4830},
    {"city": "Quitumbe (Quito)", "province": "Pichincha", "lat": -0.2900, "lon": -78.5500},
    {"city": "Terminal Guayaquil", "province": "Guayas", "lat": -2.1530, "lon": -79.8870},
    {"city": "Terminal Cuenca", "province": "Azuay", "lat": -2.8950, "lon": -79.0100},
    {"city": "Terminal Riobamba", "province": "Chimborazo", "lat": -1.6680, "lon": -78.6500},

    # --- Zonas turísticas ---
    {"city": "Mitad del Mundo", "province": "Pichincha", "lat": 0.0022, "lon": -78.4558},
    {"city": "Baños de Agua Santa", "province": "Tungurahua", "lat": -1.3965, "lon": -78.4227},
    {"city": "Otavalo", "province": "Imbabura", "lat": 0.2340, "lon": -78.2620},
    {"city": "Cotopaxi (Parque Nacional)", "province": "Cotopaxi", "lat": -0.6839, "lon": -78.4374},
    {"city": "Quilotoa (Laguna)", "province": "Cotopaxi", "lat": -0.8610, "lon": -78.8960},
    {"city": "Mindo", "province": "Pichincha", "lat": -0.0500, "lon": -78.7800},
    {"city": "Papallacta", "province": "Napo", "lat": -0.3667, "lon": -78.1333},
    {"city": "Vilcabamba", "province": "Loja", "lat": -4.2600, "lon": -79.2200},
    {"city": "Ingapirca", "province": "Cañar", "lat": -2.5480, "lon": -78.8740},
    {"city": "Parque Nacional Cajas", "province": "Azuay", "lat": -2.8400, "lon": -79.2200},
    {"city": "Isla Santay", "province": "Guayas", "lat": -2.2200, "lon": -79.8700},

    # --- Playas ---
    {"city": "Salinas", "province": "Santa Elena", "lat": -2.2137, "lon": -80.9671},
    {"city": "Atacames", "province": "Esmeraldas", "lat": 0.8690, "lon": -79.8290},
    {"city": "Mompiche", "province": "Esmeraldas", "lat": 0.5067, "lon": -80.0280},
    {"city": "Puerto López", "province": "Manabí", "lat": -1.5500, "lon": -80.8100},
    {"city": "Canoa", "province": "Manabí", "lat": -0.4540, "lon": -80.4540},
    {"city": "Montañita", "province": "Santa Elena", "lat": -1.8300, "lon": -80.7500},
    {"city": "Ayampe", "province": "Manabí", "lat": -1.6580, "lon": -80.8100},
    {"city": "Same", "province": "Esmeraldas", "lat": 0.8480, "lon": -79.9320},
    {"city": "Pedernales", "province": "Manabí", "lat": 0.0790, "lon": -80.0510},
    {"city": "Bahía de Caráquez", "province": "Manabí", "lat": -0.6040, "lon": -80.4170},
    {"city": "Playas (General Villamil)", "province": "Guayas", "lat": -2.6320, "lon": -80.3830},

    # --- Ciudades adicionales ---
    {"city": "Cayambe", "province": "Pichincha", "lat": 0.0400, "lon": -78.1600},
    {"city": "Sangolquí", "province": "Pichincha", "lat": -0.3340, "lon": -78.4480},
    {"city": "Durán", "province": "Guayas", "lat": -2.1700, "lon": -79.8300},
    {"city": "Milagro", "province": "Guayas", "lat": -2.1300, "lon": -79.5900},
    {"city": "Daule", "province": "Guayas", "lat": -1.8600, "lon": -79.9800},
    {"city": "Santa Rosa", "province": "El Oro", "lat": -3.4500, "lon": -79.9600},
    {"city": "Huaquillas", "province": "El Oro", "lat": -3.4800, "lon": -80.2300},
    {"city": "San Lorenzo", "province": "Esmeraldas", "lat": 1.2860, "lon": -78.8350},
    {"city": "La Maná", "province": "Cotopaxi", "lat": -0.9340, "lon": -79.2230},
    {"city": "Salcedo", "province": "Cotopaxi", "lat": -1.0460, "lon": -78.5920},
    {"city": "Pujilí", "province": "Cotopaxi", "lat": -0.9520, "lon": -78.6930},
    {"city": "Calceta", "province": "Manabí", "lat": -0.8450, "lon": -79.7980},
    {"city": "El Chaco", "province": "Napo", "lat": -0.3350, "lon": -77.8080},
]

CIUDADES_CHOICES = [
    (loc["city"], f"{loc['city']} — {loc['province']}")
    for loc in ECUADOR_LOCATIONS
]

CIUDADES_LIST = [loc["city"] for loc in ECUADOR_LOCATIONS]


def get_coordinates(city_name):
    for loc in ECUADOR_LOCATIONS:
        if loc["city"].lower() == city_name.lower():
            return loc["lat"], loc["lon"]
    return None, None
