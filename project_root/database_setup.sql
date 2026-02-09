CREATE TABLE IF NOT EXISTS bso_data (
    id SERIAL PRIMARY KEY,
    bso_week VARCHAR(50),
    submercado VARCHAR(30),
    data_inicio DATE,
    data_fim DATE,
    carga DECIMAL(15,6),
    intercambio DECIMAL(15,6),
    hidraulica DECIMAL(15,6),
    termica DECIMAL(15,6),
    eolica DECIMAL(15,6),
    solar DECIMAL(15,6),
    ena DECIMAL(10,2),
    ear DECIMAL(10,2),
    itaipu DECIMAL(15,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bso_week, submercado)
);

CREATE TABLE IF NOT EXISTS bbce_data (
    id SERIAL PRIMARY KEY,
    produto VARCHAR(50),
    data DATE,
    preco DECIMAL(10,2),
    tipo_produto VARCHAR(10),
    ano_referencia INTEGER,
    mes_inicio INTEGER,
    mes_fim INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(produto, data)
);

-- Daily negotiations by price level (keeps intra-day distribution + volume proxy).
CREATE TABLE IF NOT EXISTS bbce_trades (
    id SERIAL PRIMARY KEY,
    produto VARCHAR(50),
    data DATE,
    preco DECIMAL(10,2),
    qtd INTEGER,
    tipo_produto VARCHAR(10),
    ano_referencia INTEGER,
    mes_inicio INTEGER,
    mes_fim INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(produto, data, preco)
);

CREATE TABLE IF NOT EXISTS pld_data (
    id SERIAL PRIMARY KEY,
    regiao VARCHAR(30),
    metrica VARCHAR(20),
    periodo VARCHAR(20),
    tipo VARCHAR(20),
    valor DECIMAL(10,4),
    data_inicio DATE,
    data_fim DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regiao, data_inicio, metrica)
);

CREATE TABLE IF NOT EXISTS cmo_data (
    id SERIAL PRIMARY KEY,
    regiao VARCHAR(30),
    metrica VARCHAR(20),
    periodo VARCHAR(20),
    tipo VARCHAR(20),
    valor DECIMAL(10,4),
    data_inicio DATE,
    data_fim DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regiao, data_inicio, metrica)
);

CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    model_type VARCHAR(50),
    product_type VARCHAR(20),
    horizon VARCHAR(10),
    metrics JSONB,
    model_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    product VARCHAR(50),
    prediction_date DATE,
    horizon VARCHAR(10),
    predicted_value DECIMAL(10,2),
    confidence_interval_lower DECIMAL(10,2),
    confidence_interval_upper DECIMAL(10,2),
    trend VARCHAR(20),
    model_id INTEGER REFERENCES ml_models(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
