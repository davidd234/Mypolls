import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "./components/ui/card";
import { Button } from "./components/ui/button";


const ELECTIONS = [
  2000, 2004, 2008, 2012, 2016, 2020, 2024
];

const MOCK_RESULTS = {
  2024: [
    { name: "Nicușor Dan", value: 47.94 },
    { name: "Gabriela Firea", value: 22.33 },
    { name: "Cristian Popescu Piedone", value: 16.17 },
  ],
};

export default function App() {
  const [year, setYear] = useState(2024);

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-purple-950 text-white p-8">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl font-bold mb-6 text-center"
      >
        🧠 MyPolls – PMB Elections AI Dashboard
      </motion.h1>

      {/* Timeline */}
      <div className="flex justify-center gap-2 mb-10 flex-wrap">
        {ELECTIONS.map((y) => (
          <Button
            key={y}
            variant={year === y ? "default" : "outline"}
            onClick={() => setYear(y)}
            className="rounded-full"
          >
            {y}
          </Button>
        ))}
      </div>

      {/* Content */}
      <motion.div
        key={year}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="max-w-4xl mx-auto"
      >
        <Card className="bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl rounded-2xl">
          <CardContent className="p-6">
            <h2 className="text-2xl font-semibold mb-4">
              Alegeri PMB {year}
            </h2>

            {MOCK_RESULTS[year] ? (
              <div className="space-y-4">
                {MOCK_RESULTS[year].map((c) => (
                  <div key={c.name}>
                    <div className="flex justify-between mb-1">
                      <span>{c.name}</span>
                      <span>{c.value}%</span>
                    </div>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${c.value}%` }}
                      transition={{ duration: 1 }}
                      className="h-3 rounded-full bg-gradient-to-r from-cyan-400 via-purple-500 to-pink-500"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 italic">
                Nu există date ML pentru această ediție (demo UI only).
              </p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      <footer className="text-center text-sm text-gray-400 mt-12">
        Experimental AI polling dashboard · visual prototype
      </footer>
    </div>
  );
}
