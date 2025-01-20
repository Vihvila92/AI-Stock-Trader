CREATE DATABASE IF NOT EXISTS StockDB;
USE StockDB;

CREATE TABLE Stocks (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    ticker_symbol VARCHAR(10) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(255),
    industry VARCHAR(255),
    market_cap BIGINT,
    ipo_date DATE
);

CREATE TABLE StockPrices (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT,
    date DATE,
    open_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    volume BIGINT,
    FOREIGN KEY (stock_id) REFERENCES Stocks(stock_id)
);

CREATE TABLE StockNews (
    news_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT,
    date DATE,
    headline VARCHAR(255),
    source VARCHAR(255),
    content TEXT,
    sentiment_score DECIMAL(5, 2),
    FOREIGN KEY (stock_id) REFERENCES Stocks(stock_id)
);

CREATE TABLE StockAnalytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT,
    date DATE,
    moving_average DECIMAL(10, 2),
    rsi DECIMAL(5, 2),
    macd DECIMAL(10, 2),
    bollinger_bands DECIMAL(10, 2),
    sentiment_analysis DECIMAL(5, 2),
    FOREIGN KEY (stock_id) REFERENCES Stocks(stock_id)
);

CREATE TABLE StockTransactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    stock_id INT,
    date DATE,
    transaction_type ENUM('buy', 'sell'),
    quantity INT,
    price DECIMAL(10, 2),
    FOREIGN KEY (stock_id) REFERENCES Stocks(stock_id)
);

-- Indexes
CREATE INDEX idx_ticker_symbol ON Stocks(ticker_symbol);
CREATE INDEX idx_date_stockprices ON StockPrices(date);
CREATE INDEX idx_date_stocknews ON StockNews(date);
CREATE INDEX idx_date_stockanalytics ON StockAnalytics(date);