# 🧾 InnoVentory

> **A smart, web-based inventory and business management system built for small and medium enterprises (SMEs).**

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.x-green?logo=django)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)

---

## 📘 Overview

**InnoVentory** is a web-based system designed to simplify inventory tracking, sales monitoring, and business record-keeping for small and medium enterprises.  
It integrates an intuitive user interface with a robust backend to:

- ✅ Streamline daily operations  
- 🧠 Reduce human error  
- 📊 Provide real-time data insights  
- 👥 Manage users and roles efficiently

---

## 🧩 Tech Stack

| Layer | Technology |
|:------|:------------|
| **Frontend** | HTML, CSS, JavaScript |
| **Backend** | Python (Django Framework) |
| **Database** | MySQL |
| **Version Control** | Git & GitHub |

---

<details>
<summary>⚙️ <b>Setup & Run Instructions</b></summary>

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/<your-repo>/innoventory.git
cd innoventory
```


###2️⃣ Create and Activate a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # For Windows
# or
source venv/bin/activate     # For macOS/Linux
```

###3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

4️⃣ Configure the Database
Edit your settings.py
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'innoventory_db',
        'USER': 'root',
        'PASSWORD': '<your-password>',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

5️⃣ Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

6️⃣ Create a Superuser
```bash
python manage.py createsuperuser
```

7️⃣ Run the Server
```bash
python manage.py runserver
```
Now open your browser and go to 👉 http://127.0.0.1:8000

</details>

👥 Team Members
Michelle Marie P. Habon - Business Analyst - michellemarie.habon@cit.edu
Tovi Joshua J. Hermosisima - Scrum Master - tovijoshua.hermosisima@cit.edu
Ashley N. Igonia - Product Owner - ashley.igonia@cit.edu

Kenn Xavier C. Dabon - Developer - kenn.dabon@cit.edu
Shinely Marie R. Embalsado - Developer - shinelymarie.embalsado@cit.edu
Michaela Ma. Alexa D. Estrera - Lead Developer - michaelamaalexa.estrera@cit.edu
