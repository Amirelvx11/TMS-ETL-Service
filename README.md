# TMS-ETL-Service ⚙️
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


## Description 📝
The TMS-ETL-Service is a Python-based ETL (Extract, Transform, Load) service designed to extract data from a source MySQL database, transform it, and load it into a target **Microsoft SQL** Server database. It is containerized using Docker for easy deployment and uses cron for scheduled execution every 12 hours. The service processes data related to products and their associated guaranties, ensuring data synchronization between the source and target databases.



## Table of Contents 🗺️
1. [Description](#description-)
2. [Features](#features-)
3. [Tech Stack](#tech-stack-)
4. [Installation](#installation-)
5. [Usage](#usage-)
6. [How to use](#how-to-use-)
7. [Project Structure](#project-structure-)
8. [Contributing](#contributing-)
9. [License](#license-)
10. [Contact](#contact-)



## Features ✨
-   **Data Extraction**: Extracts data from a source MySQL database (`h_tool.tab_reader_barcode`).
-   **Data Transformation**: Transforms the extracted data, including mapping operating system and manager versions to their respective IDs, standardizing IMEI and production date formats.
-   **Data Loading**: Loads the transformed data into a target SQL Server database (`mfu.Product` and `mfu.Guaranty`).
-   **Scheduled Execution**: Utilizes cron to schedule the ETL process to run every 12 hours.
-   **Lookup Maps**: Fetches lookup maps for `Operating System` and `Manager` titles from the target database.
-   **Product & Guaranty Insertion**: Manages the `Product` and `Guaranty` table by inserting new records based on new products.
-   **Dockerized**: Containerized for easy deployment using Docker and Docker Compose.
-   **Logging**: Logs ETL process execution to `/var/log/etl.log`.



## Tech Stack 💻
-   **Language**: Python
-   **Frameworks**: SQLAlchemy, Pandas
-   **Containerization**: Docker, Docker Compose
-   **Databases**: MySQL (Source), Microsoft SQL Server (Target)
-   **Other**: python-dotenv, pyodbc



## Installation 🔧
1.  **Clone the repository**: 

    ```bash
    git clone https://github.com/Amirelvx11/TMS-ETL-Service.git
    cd TMS-ETL-Service
    ```

2.  **Set up environment variables**: 

    Create a `.env` file in the root directory with the following variables:

    ```
    # Using mysqlclient (mysqldb)
    SOURCE_DB=mysql+mysqldb://user:password@host:3306/db?charset=utf8mb4

    # Using pyodbc (recommended: ODBC Driver 18)
    TARGET_DB=mssql+pyodbc://user:password@host:1433/db?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=no&TrustServerCertificate=yes&LoginTimeout=5&ConnectionTimeout=5
    ```

    Replace `<source_db_connection_string>` (MySQL connection string) and `<target_db_connection_string>` (SQL Server connection string) with your actual database connection strings.

    Example connection strings:
    -   `SOURCE_DB=mysql+mysqlconnector://user:password@host/database`
    -   `TARGET_DB=mssql+pyodbc://user:password@dsn`

3.  **Install dependencies**: 

    ```bash
    pip install --no-cache-dir -r requirements.txt
    ```

4.  **Build and run the Docker container**: 

    ```bash
    docker compose up --build
    ```



## Usage 💡
1.  **Running the ETL process**: 

    The ETL process is scheduled to run every 12 hours via cron. The cron configuration is set up in the `Dockerfile`:

    ```
    RUN echo "0 */12 * * * python /app/main.py >> /var/log/etl.log 2>&1" > /etc/cron.d/tms_cron
    ```

    This command schedules the `main.py` script to run every 12 hours and logs the output to `/var/log/etl.log`.

2.  **Manual execution**: 

    You can also manually run the ETL process by executing the `main.py` script inside the Docker container:

    ```bash
    docker exec -it tms_etl python /app/main.py
    ```

3.  **Real World Use Case**:

    Imagine a scenario where a company needs to synchronize product data between a MySQL database (`h_tool`) and a SQL Server database (`mfu`). The MySQL database (`h_tool.tab_reader_barcode`) contains raw product information that needs to be cleaned, transformed, and loaded into the SQL Server database (`mfu.Product` and `mfu.Guaranty`). The `TMS-ETL-Service` automates this process by:

    -   **Extracting** new product entries from `h_tool.tab_reader_barcode`.
    -   **Transforming** the data by mapping OS and Manager versions to their corresponding IDs, and standardizing IMEI and production date formats.
    -   **Loading** the transformed data into `mfu.Product` and creating corresponding warranty records in `mfu.Guaranty`.

    This ensures that the `mfu` database always has the latest, correctly formatted product data, which can then be used for other business processes such as sales, inventory management, and customer support.



## How to use 🚀
To utilize the TMS-ETL-Service effectively, follow these steps:

1.  **Configure Database Connections**: Ensure that the `.env` file contains the correct connection strings for both the source (MySQL) and target (SQL Server) databases. This includes the user credentials, host, and database name.

2.  **Understand Data Transformation**: The service transforms data by mapping OS and Manager versions to their corresponding IDs. Make sure the lookup maps in the `mfu` database for `OperatingSystem` and `Manager` are up-to-date.

3.  **Monitor ETL Process**: The ETL process runs automatically every 12 hours. Check the `/var/log/etl.log` file inside the Docker container for any errors or logs.

4.  **Manual Execution (if needed)**: If you need to run the ETL process manually, use the `docker exec` command to execute the `main.py` script inside the container.

5.  **Verify Data**: After the ETL process completes, verify that the new product entries and their associated warranty records have been correctly inserted into the `mfu.Product` and `mfu.Guaranty` tables in the target database.



## Project Structure 📁
```
TMS-ETL-Service/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── main.py
└── src/
    ├── __init__.py
    ├── config.py
    ├── fetch.py
    ├── insert.py
    ├── logger.py
    └── transform.py
```

-   `Dockerfile`: Defines the Docker image for the service, including installing dependencies and setting up the cron job.
-   `docker-compose.yml`: Defines the Docker Compose configuration for running the service with environment variables.
-   `requirements.txt`: Lists the Python dependencies for the project, such as `SQLAlchemy`, `pandas`, `pyodbc`, and `python-dotenv`.
-   `README.md`: Documentation for the project (this file).
-   `main.py`: Entry point for the ETL process. It orchestrates the data fetching, transformation, and loading.
-   `src/`: Contains the Python modules for the ETL process:
    -   `config.py`: Configuration settings for database connections using environment variables.
    -   `fetch.py`: Functions for fetching data from the source MySQL database and lookup maps from the target SQL Server database.
    -   `insert.py`: Functions for inserting transformed data into the target SQL Server database, including product and guaranty information.
    -   `logger.py`: Defines the logger for the application
    -   `transform.py`: Functions for transforming the extracted data to fit the target database schema.



## Contributing 🤝
Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with descriptive messages.
4.  Submit a pull request.



## License 📝
This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/licenses/MIT) file for details.



## Contact 📩

- **Maintainer:** [Amir Jamshidi](mailto:amirjamshidi.developer@gmail.com)
- **Project Repository:** [TMS-ETL-Service](https://github.com/Amirelvx11/TMS-ETL-Service)

⭐️ If you like this project, please give it a star on GitHub! It helps others discover it.
