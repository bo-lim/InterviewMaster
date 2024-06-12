'use client';
import Link from 'next/link'
import { Button } from '../../components/ui/button'
import { Download, Send } from 'lucide-react';

const Custom = () => {
  // const [categories, setCategories] = useState(uniqueCategories);
  // console.log(categories);
  return (
    <section className='py-12 xl:py-24 h-[84vh] xl:pt-28 bg-hero bg-no-repeat bg-bottom bg-cover dark:bg-none'>
      <div className='container mx-auto'>
        <div className='flex justify-between gap-x-8'>
          <div>
            <div className='text-sm uppercase font-semibold mb-4 text-primary tracking-[4px]'>
              Web Service
            </div>
            <h1 className="section-title mb-8 xl:mb-16 text-center mx-auto">
              자소서 기반 면접 Service  
            </h1>

            <p className='subtitle max-w-[490px] mx-auto xl:mx-0'>
              here is custom page
            </p>
            <div>
            <Link href='/likework'>
                <Button className='gap-x-2'>
                  Start<Send size={18}/>
                </Button>
            </Link>
             
            </div>
          </div>
        </div>
         
      </div>
    </section>
  );
};
export default Custom;
