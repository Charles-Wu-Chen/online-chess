declare module 'chess.js' {
  export class Chess {
    constructor(fen?: string);
    move(move: string | { from: string; to: string; promotion?: string }): { color: string; from: string; to: string; flags: string; piece: string; san: string } | null;
    fen(): string;
    isGameOver(): boolean;
    isCheckmate(): boolean;
    // Add other methods you're using from Chess.js
  }
}