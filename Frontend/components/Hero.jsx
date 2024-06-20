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
    <section className='py-12 xl:py-24 h-[84vh] xl:pt-28 bg-hero bg-no-repeat bg-bottom bg-cover dark:bg-none'>
      <div className='container mx-auto'>
        <div className='flex justify-between gap-x-8'>
          <div>
            <div className='text-sm uppercase font-semibold mb-4 text-primary tracking-[4px]'>
              Web Devoloper
            </div>
            <h1 className='h1 mb-4'>
              Welcome to <span className='block'>IM</span>
            </h1>
            <p className='subtitle max-w-[490px] mx-auto xl:mx-0'>
              here is Main page
            </p>
            <div>
              <Link href='/login'>
                <Button className='gap-x-2'>
                  Start<Send size={18}/>
                  </Button>
              </Link>
             
            </div>
          </div>
          <div className='hidden xl:flex relative'>
            <div className='bg-hero_shape2_dark dark:bg-hero_shape2_light w-[500px] h-[500px] bg-no-repeat absolute -top-1 -right-2 bg-opacity-50'></div>
            <DevImg 
              containerStyles=' w-[500px] h-[450px] bg-no-repeat relative bg-bottom'
              imgSrc='/hero/maininterview.png'/>
          </div>
        
        </div>
          <div className='hidden md:flex absolute left-2/4 bottom-44 xl:bottom-12 animate-bounce'>
            <RiArrowDownSLine className='text-3xl text-primary' />
          </div>
      </div>
    </section>
  );
};
export default Hero
