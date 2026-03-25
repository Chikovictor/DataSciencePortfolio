# Victor Mwadzombo – Portfolio Website

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional personal portfolio website built with **Django**, showcasing data science projects, case studies, and certifications. Designed to provide a seamless user experience for viewers to explore my work and get in touch.

## 🚀 Features

- **Project Case Studies**: Detailed breakdowns of data science projects, including problem statements, data, approaches, and results.
- **Dynamic Reviews**: A testimonial section where clients and collaborators can leave feedback (moderated via the admin panel).
- **Events & Highlights**: Showcase recent events, talks, or milestones with dedicated images and descriptions.
- **Certifications**: A curated list of professional certifications with direct verification links.
- **Contact Form**: Integrated contact form for direct inquiries, with rate-limiting and duplicate protection.
- **Admin Dashboard**: Secure custom admin panel to manage all site content dynamically.
- **SEO Optimized**: Semantic HTML and meta tags for better search engine visibility.

## 🛠️ Tech Stack

- **Backend**: Django (Python)
- **Database**: SQLite (Production-ready for PythonAnywhere free tier)
- **Frontend**: HTML5, CSS3 (Vanilla), JavaScript
- **Deployment**: PythonAnywhere

## 💻 Local Setup

To run this project locally, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/[YOUR_USERNAME]/[YOUR_REPO_NAME].git
   cd [YOUR_REPO_NAME]
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```
   *Access the site at `http://127.0.0.1:8000/` and the admin panel at `http://127.0.0.1:8000/secure-admin/`.*

## ☁️ Deployment

This project is configured for deployment on **PythonAnywhere**:
- **Static Files**: Run `python manage.py collectstatic` on the server.
- **Environment Variables**: Configure `DJANGO_SECRET_KEY`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` in the Web tab.
- **Email**: Note that PythonAnywhere free tier requires a transactional email service (like SendGrid) for SMTP.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📬 Contact

- **Name**: Victor  Mwadzombo
- **Email**: [myportfolio332@gmail.com](mailto:myportfolio332@gmail.com)
- **Live Site**: [yourusername.pythonanywhere.com](https://yourusername.pythonanywhere.com)
- **LinkedIn**: [LinkedIn Profile](https://www.linkedin.com/in/victor-mwadzombo-95a026291/)
