import { source } from '@/lib/source';
import { DocsLayout } from '@/components/layout/notebook';
import { baseOptions } from '@/lib/layout.shared';


export default function Layout({ children }: LayoutProps<'/docs'>) {
  const base = baseOptions();

  return (
    <DocsLayout tree={source.getPageTree()} {...base} nav={{
        ...base.nav,
        title: (
          <>
            {/* {logo} */}
            <span className="font-medium in-[.uwu]:hidden max-md:hidden">Chr3D</span>
          </>
        ),
      }}>
      {children}
    </DocsLayout>
  );
}