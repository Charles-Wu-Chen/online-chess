# Online Chess Frontend

This is the frontend project for the online chess application, using React and react-chessboard.

## Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)

## Installation

1. Navigate to the project directory:
   ```bash
   cd frontend
   ```

2. Install all dependencies:
   ```bash
   npm install
   ```

3. Install chess-specific dependencies:
   ```bash
   npm install react-chessboard chess.js react-dnd react-dnd-html5-backend react-scripts@latest
   ```

## Running the Development Server

To start the development server, run:

```bash
npm start
```


This will start the server on `http://localhost:3000`. The page will reload if you make edits to the source files.

## Building for Production

To create a production build, run:

npm run build

This will create a `build` folder with the optimized production build of your app.

## Serving the Production Build

To serve the production build locally:

1. Install `serve` globally (if not already installed):
   ```bash
   npm install -g serve
   ```

2. Serve the production build:
   ```bash
   serve -s build
   ```

This will serve your production build, typically at `http://localhost:5000`.
