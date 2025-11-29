# TMS-ETL-Service ⚙️
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



## Description 📝
The TMS-ETL-Service is a Python-based ETL (Extract, Transform, Load) service designed to extract data from a source database, transform it, and load it into a target database. It is containerized using Docker for easy deployment and uses cron for scheduled execution. The service is designed to process data related to products and their associated guaranties.



## Table of Contents 🗺️
1.  [Features](#features-%EF%B8%8F)
2.  [Tech Stack](#tech-stack-%E2%9A%9B)
3.  [Installation](#installation-%E2%9A%A0)
4.  [Usage](#usage-%F0%9F%9A%80)
5.  [Project Structure](#project-structure-%F0%9F%93%81)
6.  [Contributing](#contributing-%E2%9C%8D)
7.  [License](#license-%F0%9F%93%9F)
8.  [Important Links](#important-links-%F0%9F%94%97)
9.  [Footer](#footer-%E2%9A%A9)



## Features ✨
-   **Data Extraction**: Extracts data from a source SQL Server database (`h_tool.tab_reader_barcode`).
-   **Data Transformation**: Transforms the extracted data, including mapping operating system and manager versions to their respective IDs.
-   **Data Loading**: Loads the transformed data into a target SQL Server database (`mfu.Product` and `mfu.Guaranty`).
-   **Scheduled Execution**: Utilizes cron to schedule the ETL process to run every 12 hours.
-   **Lookup Maps**: Fetches lookup maps for Operating System and Manager titles.
-   **Guaranty insertion**: Manages the `Guaranty` table based on new products.
-   **Dockerized**: Containerized for easy deployment using Docker and Docker Compose.
-   **Logging**: Logs ETL process execution to `/var/log/etl.log`.



## Tech Stack 🛠️
-   **Language**: Python
-   **Frameworks**: SQLAlchemy, Pandas
-   **Containerization**: Docker, Docker Compose
-   **Database**: Microsoft SQL Server - My SQL Server
-   **Other**: python-dotenv, pyodbc



## Installation ⚙️
1.  **Clone the repository**:

    ```bash
    git clone https://github.com/Amirelvx11/TMS-ETL-Service.git
    cd TMS-ETL-Service
    ```

2.  **Set up environment variables**:

    Create a `.env` file in the root directory with the following variables:

    ```
    SOURCE_DB=<source_db_connection_string>
    TARGET_DB=<target_db_connection_string>
    ```

    Replace `<source_db_connection_string>` and `<target_db_connection_string>` with your actual database connection strings.

3.  **Install dependencies**:

    ```bash
    pip install --no-cache-dir -r requirements.txt
    ```

4.  **Build and run the Docker container**:

    ```bash
    docker-compose up --build
    ```



## Usage 🚀
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

    Imagine a scenario where a company needs to synchronize product data between two SQL Server databases, `h_tool` (source) and `mfu` (target). The source database (`h_tool.tab_reader_barcode`) contains raw product information that needs to be cleaned, transformed, and loaded into the target database (`mfu.Product` and `mfu.Guaranty`). The `TMS-ETL-Service` automates this process by:

    -   **Extracting** new product entries from `h_tool.tab_reader_barcode`.
    -   **Transforming** the data by mapping OS and Manager versions to their corresponding IDs, and standardizing IMEI and production date formats.
    -   **Loading** the transformed data into `mfu.Product` and creating corresponding warranty records in `mfu.Guaranty`.

    This ensures that the `mfu` database always has the latest, correctly formatted product data, which can then be used for other business processes such as sales, inventory management, and customer support.



## Project Structure 🏗️
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
    └── transform.py
```

-   `Dockerfile`: Defines the Docker image for the service.
-   `docker-compose.yml`: Defines the Docker Compose configuration for running the service.
-   `requirements.txt`: Lists the Python dependencies for the project.
-   `README.md`: Documentation for the project.
-   `main.py`: Entry point for the ETL process.
-   `src/`: Contains the Python modules for the ETL process:
    -   `config.py`: Configuration settings for database connections.
    -   `fetch.py`: Functions for fetching data from the source database.
    -   `insert.py`: Functions for inserting data into the target database.
    -   `transform.py`: Functions for transforming the extracted data.



## Contributing 🤝
Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with descriptive messages.
4.  Submit a pull request.



## License 📝
This project is licensed under the MIT License - see the [LICENSE](https://opensource.org/licenses/MIT) file for details.



## Important Links 🔗
-   **Repository**: [https://github.com/Amirelvx11/TMS-ETL-Service](https://github.com/Amirelvx11/TMS-ETL-Service)



## Footer ©
-   **Repository**: [TMS-ETL-Service](https://github.com/Amirelvx11/TMS-ETL-Service)
-   **Author**: [Amirelvx11](https://github.com/Amirelvx11)

⭐️ If you found this project helpful, please give it a star! Fork it to contribute and feel free to open issues for any questions or suggestions.
