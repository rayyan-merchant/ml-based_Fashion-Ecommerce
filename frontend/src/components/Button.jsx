import React from "react";

export default function Button({ children, onClick, className = "", variant = "soft", ...props }) {
  // variant 'soft' => rounded soft neutral button with accent
  const base = "btn";
  const soft = "btn-soft";
  const classes = `${base} ${soft} ${className}`;

  return (
    <button onClick={onClick} className={classes} {...props}>
      {children}
    </button>
  );
}
