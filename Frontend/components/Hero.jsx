import Link from 'next/link'
import { Button } from './ui/button'
import { Download, Send } from 'lucide-react';


import {
  RiBriefcase4Fill,
  RiTeamFill,
  RiTodoFill,
  RiArrowDownSLine,
} from 'react-icons/ri';

import DevImg from './Devlmg';
import Badge from './Badge';
import Socials from './Socials';

const Hero = () => {
  return (
    <section className='py-12 xl:py-24 h-[84vh] xl:pt-28 bg-blue-100'>
      <dic className='container mx-auto'>
        <div className='flex justify-between gap-x-8'>
          <div>test</div>
          <div>image</div>
        </div>
      </dic>
      <div className='hidden md:flex absolute left-2/4 bottom-44 xl:bottom-12 animate-bounce'>
        <RiArrowDownSLine className='text-3xl text-primary' />
      </div>
    </section>
  );
};
export default Hero