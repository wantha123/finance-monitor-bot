# config.py
import os

CONFIG = {
    "stocks": {
        # Tech & Gaming
        "PARRO.PA": {
            "name": "Parrot",
            "thresholds": {"high": 15.0, "low": 3.0, "change_percent": 15.0}
        },
        "STMPA.PA": {
            "name": "STMicroelectronics",
            "thresholds": {"high": 35.0, "low": 15.0, "change_percent": 8.0}
        },
        "ALCJ.PA": {
            "name": "CROSSJECT",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 20.0}
        },
        "UBI.PA": {
            "name": "Ubisoft",
            "thresholds": {"high": 25.0, "low": 8.0, "change_percent": 12.0}
        },
        "ALDNE.PA": {
            "name": "DON'T NOD",
            "thresholds": {"high": 30.0, "low": 10.0, "change_percent": 15.0}
        },
        "ALLDL.PA": {
            "name": "Groupe LDLC",
            "thresholds": {"high": 60.0, "low": 30.0, "change_percent": 10.0}
        },
        "ALLIX.PA": {
            "name": "Wallix Group SA",
            "thresholds": {"high": 20.0, "low": 5.0, "change_percent": 15.0}
        },
        "DEEZR.PA": {
            "name": "Deezer SA",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        "AL2SI.PA": {
            "name": "2CRSi",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}
        },
        
        # Green Energy & Environment
        "ALEUP.PA": {
            "name": "Europlasma",
            "thresholds": {"high": 1.0, "low": 0.05, "change_percent": 25.0}
        },
        "ALDRV.PA": {
            "name": "Drone Volt SA",
            "thresholds": {"high": 0.5, "low": 0.05, "change_percent": 20.0}
        },
        "ALHRS.PA": {
            "name": "Hydrogen Refueling Solutions",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        "ALDLT.PA": {
            "name": "Delta Drone SA",
            "thresholds": {"high": 1.0, "low": 0.1, "change_percent": 20.0}
        },
        "ALLHY.PA": {
            "name": "Lhyfe SA",
            "thresholds": {"high": 15.0, "low": 5.0, "change_percent": 15.0}
        },
        "ALCRB.PA": {
            "name": "Carbios",
            "thresholds": {"high": 15.0, "low": 3.0, "change_percent": 15.0}
        },
        "ARVEN.PA": {
            "name": "Arverne Group",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}
        },
        "ALWTR.PA": {
            "name": "Osmosun SA",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        
        # Healthcare & Biotech
        "ALCAR.PA": {
            "name": "Carmat",
            "thresholds": {"high": 15.0, "low": 3.0, "change_percent": 15.0}
        },
        "ALNFL.PA": {
            "name": "NFL Biosciences SA",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        "VALN.PA": {
            "name": "Valneva SE",
            "thresholds": {"high": 10.0, "low": 2.0, "change_percent": 15.0}
        },
        
        # Large Caps & Industrial
        "OVH.PA": {
            "name": "OVH Groupe SAS",
            "thresholds": {"high": 20.0, "low": 10.0, "change_percent": 5.0}
        },
        "ATO.PA": {
            "name": "Atos",
            "thresholds": {"high": 5.0, "low": 0.5, "change_percent": 15.0}
        },
        "MT.PA": {
            "name": "ArcelorMittal",
            "thresholds": {"high": 30.0, "low": 15.0, "change_percent": 8.0}
        },
        "ENGI.PA": {
            "name": "Engie",
            "thresholds": {"high": 18.0, "low": 10.0, "change_percent": 6.0}
        },
        "STLAP.PA": {
            "name": "Stellantis",
            "thresholds": {"high": 20.0, "low": 8.0, "change_percent": 10.0}
        },
        "EN.PA": {
            "name": "Bouygues",
            "thresholds": {"high": 40.0, "low": 25.0, "change_percent": 6.0}
        },
        "CA.PA": {
            "name": "Carrefour",
            "thresholds": {"high": 18.0, "low": 12.0, "change_percent": 6.0}
        },
        "FRVIA.PA": {
            "name": "Forvia",
            "thresholds": {"high": 20.0, "low": 10.0, "change_percent": 10.0}
        },
        
        # Services & Consumer
        "KOF.PA": {
            "name": "Kaufman & Broad",
            "thresholds": {"high": 40.0, "low": 20.0, "change_percent": 10.0}
        },
        "ETL.PA": {
            "name": "Eutelsat Communications",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 12.0}
        },
        "ELIOR.PA": {
            "name": "Elior Group",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 12.0}
        },
        "SBT.PA": {
            "name": "Œneo",
            "thresholds": {"high": 15.0, "low": 8.0, "change_percent": 10.0}
        },
        "PLX.PA": {
            "name": "Pluxee NV",
            "thresholds": {"high": 30.0, "low": 20.0, "change_percent": 8.0}
        },
        "CRI.PA": {
            "name": "Chargeurs",
            "thresholds": {"high": 20.0, "low": 10.0, "change_percent": 10.0}
        },
        "ALVIN.PA": {
            "name": "Vinpai SA",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}
        },
        "FDJ.PA": {
            "name": "FDJ (La Française des Jeux)",
            "thresholds": {"high": 40.0, "low": 30.0, "change_percent": 8.0}
        },
        "ALLPL.PA": {
            "name": "Lepermislibre",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        }
    },
    "crypto": {
        # Top Market Cap Cryptos
        "ETH": {
            "name": "Ethereum",
            "thresholds": {"high": 4000.0, "low": 2000.0, "change_percent": 8.0}
        },
        "SOL": {
            "name": "Solana",
            "thresholds": {"high": 180.0, "low": 90.0, "change_percent": 10.0}
        },
        "DOGE": {
            "name": "Dogecoin",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 15.0}
        },
        "ADA": {
            "name": "Cardano",
            "thresholds": {"high": 1.0, "low": 0.3, "change_percent": 12.0}
        },
        "LINK": {
            "name": "Chainlink",
            "thresholds": {"high": 30.0, "low": 10.0, "change_percent": 12.0}
        },
        "ZEC": {
            "name": "Zcash",
            "thresholds": {"high": 100.0, "low": 30.0, "change_percent": 15.0}
        },
        "PEPE": {
            "name": "Pepe",
            "thresholds": {"high": 0.00003, "low": 0.000005, "change_percent": 20.0}
        },
        "UNI": {
            "name": "Uniswap",
            "thresholds": {"high": 15.0, "low": 5.0, "change_percent": 15.0}
        },
        "CRO": {
            "name": "Cronos",
            "thresholds": {"high": 0.2, "low": 0.05, "change_percent": 15.0}
        },
        "MNT": {
            "name": "Mantle",
            "thresholds": {"high": 1.5, "low": 0.5, "change_percent": 15.0}
        },
        "RENDER": {
            "name": "Render",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}
        },
        "FET": {
            "name": "Artificial Superintelligence Alliance",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 15.0}
        },
        "ARB": {
            "name": "Arbitrum",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 15.0}
        },
        "FIL": {
            "name": "Filecoin",
            "thresholds": {"high": 10.0, "low": 3.0, "change_percent": 15.0}
        },
        "ALGO": {
            "name": "Algorand",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 15.0}
        },
        "MKR": {
            "name": "Sky",
            "thresholds": {"high": 2000.0, "low": 800.0, "change_percent": 12.0}
        },
        "GRT": {
            "name": "The Graph",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 15.0}
        },
        "ENS": {
            "name": "Ethereum Name Service",
            "thresholds": {"high": 50.0, "low": 15.0, "change_percent": 15.0}
        },
        "GALA": {
            "name": "Gala",
            "thresholds": {"high": 0.1, "low": 0.02, "change_percent": 20.0}
        },
        "FLOW": {
            "name": "Flow",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 15.0}
        },
        "MANA": {
            "name": "Decentraland",
            "thresholds": {"high": 1.0, "low": 0.3, "change_percent": 15.0}
        },
        
        # Layer 2 & New Technologies
        "STRK": {
            "name": "Starknet",
            "thresholds": {"high": 3.0, "low": 1.0, "change_percent": 15.0}
        },
        "EIGEN": {
            "name": "EigenLayer",
            "thresholds": {"high": 10.0, "low": 2.0, "change_percent": 15.0}
        },
        "EGLD": {
            "name": "MultiversX",
            "thresholds": {"high": 50.0, "low": 20.0, "change_percent": 12.0}
        },
        "MOVE": {
            "name": "Movement",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 20.0}
        },
        "LPT": {
            "name": "Livepeer",
            "thresholds": {"high": 30.0, "low": 10.0, "change_percent": 15.0}
        },
        "MOG": {
            "name": "Mog Coin",
            "thresholds": {"high": 0.000005, "low": 0.000001, "change_percent": 25.0}
        },
        "MASK": {
            "name": "Mask Network",
            "thresholds": {"high": 5.0, "low": 2.0, "change_percent": 15.0}
        },
        "MINA": {
            "name": "Mina",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 15.0}
        },
        
        # Utility & Platform Tokens
        "BAT": {
            "name": "Basic Attention Token",
            "thresholds": {"high": 0.5, "low": 0.15, "change_percent": 15.0}
        },
        "ENJ": {
            "name": "Enjin Coin",
            "thresholds": {"high": 0.5, "low": 0.15, "change_percent": 15.0}
        },
        "COTI": {
            "name": "COTI",
            "thresholds": {"high": 0.3, "low": 0.05, "change_percent": 20.0}
        },
        "BAND": {
            "name": "Band Protocol",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 15.0}
        },
        "UMA": {
            "name": "UMA",
            "thresholds": {"high": 5.0, "low": 1.5, "change_percent": 15.0}
        },
        "BICO": {
            "name": "Biconomy",
            "thresholds": {"high": 1.0, "low": 0.3, "change_percent": 20.0}
        },
        "KEEP": {
            "name": "Keep Network",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 20.0}
        },
        "POWR": {
            "name": "Powerledger",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 20.0}
        },
        "AUDIO": {
            "name": "Audius",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 20.0}
        },
        "RLC": {
            "name": "iExec RLC",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 15.0}
        },
        
        # Gaming & Emerging
        "SAGA": {
            "name": "Saga",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        "CTSI": {
            "name": "Cartesi",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 20.0}
        },
        "SCRT": {
            "name": "Secret",
            "thresholds": {"high": 1.0, "low": 0.3, "change_percent": 15.0}
        },
        "TNSR": {
            "name": "Tensor",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 20.0}
        },
        "C98": {
            "name": "Coin98",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 20.0}
        },
        "OGN": {
            "name": "Origin Protocol",
            "thresholds": {"high": 0.3, "low": 0.05, "change_percent": 20.0}
        },
        "RAD": {
            "name": "Radworks",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        "NYM": {
            "name": "NYM",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 20.0}
        },
        "ARPA": {
            "name": "ARPA",
            "thresholds": {"high": 0.2, "low": 0.03, "change_percent": 20.0}
        },
        "ALCX": {
            "name": "Alchemix",
            "thresholds": {"high": 50.0, "low": 15.0, "change_percent": 15.0}
        },
        
        # Gaming Ecosystems
        "ATLAS": {
            "name": "Star Atlas",
            "thresholds": {"high": 0.01, "low": 0.003, "change_percent": 25.0}
        },
        "POLIS": {
            "name": "Star Atlas DAO",
            "thresholds": {"high": 1.0, "low": 0.2, "change_percent": 20.0}
        },
        
        # DeFi & Advanced
        "PERP": {
            "name": "Perpetual Protocol",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 15.0}
        },
        "STEP": {
            "name": "Step Finance",
            "thresholds": {"high": 0.1, "low": 0.02, "change_percent": 25.0}
        },
        "RBN": {
            "name": "Robonomics.network",
            "thresholds": {"high": 5.0, "low": 1.0, "change_percent": 20.0}
        },
        "KP3R": {
            "name": "Keep3rV1",
            "thresholds": {"high": 100.0, "low": 30.0, "change_percent": 15.0}
        },
        "KEY": {
            "name": "SelfKey",
            "thresholds": {"high": 0.02, "low": 0.005, "change_percent": 25.0}
        },
        
        # Privacy & Infrastructure
        "KILT": {
            "name": "KILT Protocol",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 20.0}
        },
        "TEER": {
            "name": "Integritee Network",
            "thresholds": {"high": 0.5, "low": 0.1, "change_percent": 25.0}
        },
        "CRU": {
            "name": "Crust Shadow",
            "thresholds": {"high": 2.0, "low": 0.5, "change_percent": 20.0}
        },
        "ZEUS": {
            "name": "Zeus Network",
            "thresholds": {"high": 1.0, "low": 0.3, "change_percent": 25.0}
        },
        "MC": {
            "name": "Merit Circle",
            "thresholds": {"high": 1.0, "low": 0.2, "change_percent": 20.0}
        }
    },
    "email": {
        "enabled": True,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "from_email": os.environ.get("EMAIL_USER", "example@gmail.com"),
        "password": os.environ.get("EMAIL_PASS", "changeme"),
        "to_email": os.environ.get("EMAIL_TARGET", "recipient@example.com")
    },
    "slack": {
        "enabled": True,
        "webhook_url": os.environ.get("SLACK_WEBHOOK")
    },
    "news_api_key": os.environ.get("NEWS_API_KEY", "demo")
}