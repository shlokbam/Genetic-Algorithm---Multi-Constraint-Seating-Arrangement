# 🎓 Exam Seating Optimizer (Genetic Algorithm)

A powerful, web-based tool designed to automate and optimize exam seating arrangements. It uses a **Genetic Algorithm (GA)** to satisfy complex constraints, such as ensuring students from the same branch, subject, or division do not sit next to each other.

## 🚀 Features

- **Genetic Algorithm Engine**: Uses advanced GA operators like Tournament Selection, Order Crossover (OX), and Swap/Scramble Mutation.
- **Multi-Constraint Optimization**:
  - 🚫 Prevent same-branch adjacency (Adjacent & Diagonal).
  - 🚫 Prevent same-subject proximity.
  - 🚫 Minimize clusters of the same division.
  - 🚫 Avoid consecutive roll numbers in the same column.
- **Real-Time Progress Tracking**: Watch the AI evolve the seating plan in real-time with live fitness charts.
- **Dynamic Attendance Management**: 
  - Mark students as absent before or after a run.
  - Add late-joining students.
  - "Rerun" optimization instantly with the updated student list.
- **Modern Responsive UI**: Sleek dark-mode interface built with Vanilla CSS and JavaScript.

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **AI Engine**: Pure Python (Optimized for speed)
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JavaScript
- **Deployment**: Configured for Render/Gunicorn

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/shlokbam/Genetic-Algorithm---Multi-Constraint-Seating-Arrangement.git
   cd Genetic-Algorithm---Multi-Constraint-Seating-Arrangement
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

## 🚢 Deployment

The project is ready for deployment on **Render**. 
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

## 🧩 Project Structure

- `app.py`: Flask server and main orchestration.
- `ga_engine.py`: Core Genetic Algorithm logic.
- `fitness_module.py`: The "Brain" that calculates penalties and arrangement quality.
- `genetic_operators.py`: Implementation of mutation, crossover, and selection.
- `templates/`: Modern web frontend.

---
Developed by [Shlok Bam](https://github.com/shlokbam)
