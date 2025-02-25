# CQU Time

A FastAPI-based web application for parsing course schedules, available at [CQU Time](https://cqutime.top). You can generate `课表.ics` and import it to your device.

## Installation

To get started, ensure you have the following:


1. Clone the Repositor

```bash
git clone https://github.com/n19htfall/cqutime.git
cd cqutime
```

2. Set Up a Virtual Environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install Dependencies Using `pip`
```bash
pip install -r requirements.txt
```

4. Configure Frontend URL

- In the root directory, manually create a file named `UrlConfig.py`.

- Add the following content, replacing the URL with your frontend address:

```python
FRONTED_URL = "http://localhost:3000"  # Example for local development
```

5. Run the Application
```bash
python main.py
```

And the will be available at http://127.0.0.1:8849.

## License

This project is licensed under the MIT License. See the [License](./LICENSE) file for details.