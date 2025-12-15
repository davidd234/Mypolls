export function Button({ children, className = "", ...props }) {
  return (
    <button
      {...props}
      className={`px-4 py-2 rounded-full border border-white/20 hover:bg-white/10 transition ${className}`}
    >
      {children}
    </button>
  );
}
