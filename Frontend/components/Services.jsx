import { GanttChartSquare, Blocks, Gem } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescribe,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Description } from "@radix-ui/react-dialog";

const serviceData = [
  {
    icon: <GanttChartSquare size={72} strokeWidth={0.8} />,
    title: 'number1',
    Description: ''
  },
]

const Services = () => {
  return (
    <section className="mb-12 xl:mb-36">
      <div className="container mx-auto">
        <h2 className="section-title mb-12 xl:mb-24 text-center mx-auto">
          Service Introduction
        </h2>
        <div>
          
        </div>
      </div>
    </section>
  );
};
export default Services