"""46 curated districts/stations. tag = static geography class used for regime tagging."""
# (name, lat, lon, tag)   core = Rajeevan monsoon-core-zone district
DISTRICTS = [
    # 8 core zone
    ("Nagpur", 21.146, 79.088, "core"), ("Bhopal", 23.259, 77.413, "core"),
    ("Raipur", 21.251, 81.630, "core"), ("Jabalpur", 23.181, 79.987, "core"),
    ("Akola", 20.709, 77.002, "core"), ("Amravati", 20.933, 77.752, "core"),
    ("Aurangabad", 19.876, 75.343, "core"), ("Bhubaneswar", 20.296, 85.825, "core"),
    # 10 coastal
    ("Mumbai", 19.076, 72.878, "coastal"), ("Thiruvananthapuram", 8.524, 76.937, "coastal"),
    ("Kochi", 9.931, 76.267, "coastal"), ("Mangaluru", 12.914, 74.856, "coastal"),
    ("Panaji", 15.491, 73.828, "coastal"), ("Chennai", 13.083, 80.271, "coastal"),
    ("Visakhapatnam", 17.687, 83.219, "coastal"), ("Puri", 19.813, 85.831, "coastal"),
    ("Kolkata", 22.572, 88.364, "coastal"), ("Surat", 21.170, 72.831, "coastal"),
    # 6 orographic / hill
    ("Mahabaleshwar", 17.923, 73.658, "orographic"), ("Munnar", 10.089, 77.060, "orographic"),
    ("Madikeri", 12.424, 75.738, "orographic"), ("Ooty", 11.410, 76.695, "orographic"),
    ("Lonavala", 18.750, 73.407, "orographic"), ("Wayanad", 11.685, 76.132, "orographic"),
    # 4 Himalayan
    ("Shimla", 31.105, 77.173, "himalayan"), ("Dehradun", 30.316, 78.032, "himalayan"),
    ("Srinagar", 34.084, 74.797, "himalayan"), ("Gangtok", 27.339, 88.612, "himalayan"),
    # 4 northeast
    ("Guwahati", 26.144, 91.736, "northeast"), ("Cherrapunji", 25.270, 91.732, "northeast"),
    ("Imphal", 24.817, 93.937, "northeast"), ("Agartala", 23.831, 91.286, "northeast"),
    # 6 Gangetic plains
    ("Lucknow", 26.847, 80.947, "gangetic"), ("Patna", 25.594, 85.138, "gangetic"),
    ("Varanasi", 25.318, 82.974, "gangetic"), ("Delhi", 28.614, 77.209, "gangetic"),
    ("Kanpur", 26.449, 80.332, "gangetic"), ("Ranchi", 23.344, 85.310, "gangetic"),
    # 3 arid
    ("Jodhpur", 26.239, 73.024, "arid"), ("Bikaner", 28.022, 73.312, "arid"),
    ("Jaisalmer", 26.915, 70.916, "arid"),
    # 5 interior peninsular
    ("Hyderabad", 17.385, 78.487, "interior"), ("Bengaluru", 12.972, 77.594, "interior"),
    ("Pune", 18.520, 73.857, "interior"), ("Kurnool", 15.829, 78.037, "interior"),
    ("Madurai", 9.925, 78.120, "interior"),
]
assert len(DISTRICTS) == 46, len(DISTRICTS)
CORE = [d[0] for d in DISTRICTS if d[3] == "core"]
