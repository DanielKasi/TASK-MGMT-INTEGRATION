import { Card } from "./ui/card";
interface EmptyCardProps {
  className?:string
}

export function EmptyCard({className=""}:EmptyCardProps) {
  return (
    <Card className={`w-full h-48 bg-white overflow-hidden ${className}`}>

    </Card>
  );
}