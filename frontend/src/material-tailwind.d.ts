import 'react';

declare module '@material-tailwind/react' {
  interface ButtonProps {
    placeholder?: string;
  }
  interface CardProps {
    placeholder?: string;
  }
  interface InputProps {
    placeholder?: string;
    crossOrigin?: string;
  }
  interface SelectProps {
    placeholder?: string;
  }
  interface OptionProps {
    placeholder?: string;
  }
  interface TypographyProps {
    placeholder?: string;
  }
}
