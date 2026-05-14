import { motion } from 'framer-motion';

interface Props {
  color: string;
}

// Homenaje al NeuralGraph del cockpit — mini SVG con 6 nodos + líneas
// pulsando. Sirve como visual de "thinking".
export default function NeuralGraph({ color }: Props) {
  const nodes: Array<[number, number]> = [
    [20, 40],
    [60, 18],
    [100, 38],
    [60, 60],
    [140, 24],
    [140, 56],
  ];
  return (
    <svg viewBox="0 0 160 80" className="w-40 h-20">
      {nodes.flatMap((a, i) =>
        nodes.slice(i + 1).map((b, j) => (
          <motion.line
            key={`${i}-${j}`}
            x1={a[0]}
            y1={a[1]}
            x2={b[0]}
            y2={b[1]}
            stroke={color}
            strokeWidth={1.5}
            initial={{ opacity: 0.15 }}
            animate={{ opacity: [0.15, 0.55, 0.15] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: (i + j) * 0.07 }}
          />
        ))
      )}
      {nodes.map(([x, y], i) => (
        <motion.circle
          key={i}
          cx={x}
          cy={y}
          r={3.5}
          fill={color}
          initial={{ scale: 0.8 }}
          animate={{ scale: [0.8, 1.15, 0.8] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.1 }}
        />
      ))}
    </svg>
  );
}
