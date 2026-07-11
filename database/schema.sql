CREATE DATABASE IF NOT EXISTS diagnostic_lab;
USE diagnostic_lab;

CREATE TABLE IF NOT EXISTS Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Technician', 'Operator') NOT NULL,
    profile_photo VARCHAR(255) DEFAULT NULL,
    branch_id INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Patients (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    date DATE NOT NULL,
    referred_doctor VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Tests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    normal_range VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Test_Parameters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id INT NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    unit VARCHAR(50) DEFAULT '',
    normal_range VARCHAR(100) DEFAULT '',
    display_order INT DEFAULT 0,
    formula TEXT DEFAULT NULL,
    parameter_type VARCHAR(50) DEFAULT 'text',
    FOREIGN KEY (test_id) REFERENCES Tests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Test_Packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Test_Package_Tests (
    package_id INT NOT NULL,
    test_id INT NOT NULL,
    PRIMARY KEY (package_id, test_id),
    FOREIGN KEY (package_id) REFERENCES Test_Packages(id) ON DELETE CASCADE,
    FOREIGN KEY (test_id) REFERENCES Tests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    report_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Draft', 'Pending', 'Approved') DEFAULT 'Pending',
    total_amount DECIMAL(10, 2) DEFAULT 0.00,
    discount DECIMAL(10, 2) DEFAULT 0.00,
    paid_amount DECIMAL(10, 2) DEFAULT 0.00,
    balance_due DECIMAL(10, 2) DEFAULT 0.00,
    payment_status VARCHAR(50) DEFAULT 'Pending',
    branch_id INT DEFAULT 1,
    approved_by INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patients(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by) REFERENCES Users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Report_Parameter_Results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_id INT NOT NULL,
    parameter_id INT NOT NULL,
    result_value TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES Reports(id) ON DELETE CASCADE,
    FOREIGN KEY (parameter_id) REFERENCES Test_Parameters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ActivityLogs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    user_name VARCHAR(100) NULL,
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE SET NULL
);
